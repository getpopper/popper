import os
import time
import signal
import socket
import threading

from popper import utils as pu
from popper.cli import log as log
from popper.runner_host import HostRunner
from popper.runner_host import DockerRunner as HostDockerRunner
from popper.runner_host import SingularityRunner as HostSingularityRunner
from popper.runner_host import PodmanRunner as HostPodmanRunner


class SlurmRunner(HostRunner):
    def __init__(self, **kw):
        super(SlurmRunner, self).__init__(**kw)
        self._spawned_jobs = set()

    def __exit__(self, exc_type, exc, traceback):
        self._spawned_jobs = set()

    def _tail_output(self, out_file):
        self._out_stream_pid = set()
        _, ecode, _ = HostRunner._exec_cmd(
            ["tail", "-f", out_file], pids=self._out_stream_pid
        )
        return ecode

    def _start_out_stream(self, out_file):
        self._out_stream_thread = threading.Thread(
            target=self._tail_output, args=(out_file,)
        )
        self._out_stream_thread.start()
        # give time so that _exec_cmd puts the pid inside the self._out_stream_pid set
        time.sleep(1)

    def _stop_out_stream(self):
        if len(self._out_stream_pid) != 1:
            log.fail("Cannot find PID for tail process")
        _out_stream_pid = list(self._out_stream_pid)[0]
        try:
            os.kill(_out_stream_pid, signal.SIGKILL)
        except ProcessLookupError:
            log.warning("Tail process was stopped by some other process.")
        self._out_stream_thread.join()

    def _set_config_vars(self, step):
        self._N = self._config.resman_opts.get(step.id, {}).get("N", 1)
        self._nodelist = self._config.resman_opts.get(step.id, {}).get(
            "nodelist", socket.gethostname()
        )

    def _exec_srun(self, cmd, step, logging=False):
        self._set_config_vars(step)
        _cmd = [
            "srun",
            "-N",
            f"{self._N}",
            "--nodelist",
            self._nodelist,
            "--ntasks",
            f"{self._N}",
            "--ntasks-per-node",
            "1",
        ]
        _cmd.extend(cmd)
        log.debug(f"Command: {_cmd}")

        if self._config.dry_run:
            return 0

        _, ecode, _ = HostRunner._exec_cmd(_cmd, logging=logging)
        return ecode

    def _exec_mpi(self, cmd, step):
        self._set_config_vars(step)
        job_name = pu.sanitized_name(step.id, self._config.wid)
        mpi_cmd = ["mpirun", f"{' '.join(cmd)}"]

        job_script = os.path.join(f"{job_name}.sh")
        out_file = os.path.join(f"{job_name}.out")

        with open(out_file, "w"):
            pass

        with open(job_script, "w") as f:
            f.write("#!/bin/bash\n")
            f.write(f"#SBATCH --nodes={self._N}\n")
            f.write(f"#SBATCH --ntasks={self._N}\n")
            f.write(f"#SBATCH --ntasks-per-node=1\n")
            f.write(f"#SBATCH --nodelist={self._nodelist}\n\n")
            f.write(" ".join(mpi_cmd))

        sbatch_cmd = [
            "sbatch",
            "--job-name",
            f"{job_name}",
            "--wait",
            "--output",
            f"{out_file}",
        ]
        sbatch_cmd.extend([job_script])

        log.info(f'[{step.id}] {" ".join(sbatch_cmd)}')

        if self._config.dry_run:
            return 0

        self._spawned_jobs.add(job_name)
        self._start_out_stream(out_file)

        _, ecode, _ = HostRunner._exec_cmd(sbatch_cmd, logging=False)

        self._stop_out_stream()
        self._spawned_jobs.remove(job_name)

        return ecode

    def stop_running_tasks(self):
        for job_name in self._spawned_jobs:
            log.info(f"Cancelling job {job_name}")
            _, ecode, _ = HostRunner._exec_cmd(["scancel", "--name", job_name])
            if ecode != 0:
                log.warning(f"Failed to cancel the job {job_name}.")


class DockerRunner(SlurmRunner, HostDockerRunner):
    def __init__(self, **kw):
        super(DockerRunner, self).__init__(init_docker_client=False, **kw)

    def __exit__(self, exc_type, exc, traceback):
        pass

    def run(self, step):
        """Execute the given step via slurm in the docker engine."""
        cid = pu.sanitized_name(step.id, self._config.wid)

        build, _, img, tag, build_ctx_path = self._get_build_info(step)

        self._exec_srun(["docker", "rm", "-f", f"{cid}"], step)

        if build:
            log.info(f"[{step.id}] docker build -t {img}:{tag} {build_ctx_path}")
            self._exec_srun(
                ["docker", "build", "-t", f"{img}:{tag}", f"{build_ctx_path}"], step
            )

        elif not self._config.skip_pull and not step.skip_pull:
            log.info(f"[{step.id}] docker pull {img}:{tag}")
            self._exec_srun(["docker", "pull", f"{img}:{tag}"], step)

        log.info(f"[{step.id}] docker create -t {img}:{tag} {cid}")
        self._exec_srun(self._create_cmd(step, f"{img}:{tag}", cid), step)

        self._spawned_containers.add(cid)

        log.info(f"[{step.id}] docker start --attach {cid}")
        ecode = self._exec_srun(
            ["docker", "start", "--attach", f"{cid}"], step, logging=True
        )

        self._spawned_containers.remove(cid)
        return ecode

    def _create_cmd(self, step, img, cid):
        container_args = self._get_container_kwargs(step, img, cid)

        if "volumes" not in container_args:
            container_args["volumes"] = []
        container_args["volumes"].insert(1, "/var/run/docker.sock:/var/run/docker.sock")

        container_args.pop("detach")
        cmd = ["docker", "create"]
        cmd.extend(["--name", f"{container_args.pop('name')}"])
        cmd.extend(["--workdir", f"{container_args.pop('working_dir')}"])

        entrypoint = container_args.pop("entrypoint", None)
        if entrypoint:
            cmd.extend(["--entrypoint"])
            cmd.extend(entrypoint)

        # append volume and environment flags
        for vol in container_args.pop("volumes"):
            cmd.extend(["-v", f"{vol}"])
        for env_key, env_val in container_args.pop("environment").items():
            cmd.extend(["-e", f"{env_key}={env_val}"])

        command = container_args.pop("command")
        image = container_args.pop("image")

        # anything else is treated as a flag
        for k, v in container_args.items():
            flag = pu.key_value_to_flag(k, v)
            if flag:
                cmd.extend(flag)

        # append the image and the commands
        cmd.append(image)

        if command:
            cmd.extend(command)

        return cmd


class PodmanRunner(SlurmRunner, HostPodmanRunner):
    def __init__(self, **kw):
        super(PodmanRunner, self).__init__(init_podman_client=False, **kw)

    def __exit__(self, exc_type, exc, traceback):
        pass

    def run(self, step):
        """Execute the given step via slurm in the docker engine."""
        cid = pu.sanitized_name(step.id, self._config.wid)

        build, _, img, tag, build_ctx_path = self._get_build_info(step)

        self._exec_srun(["podman", "rm", "-f", f"{cid}"], step)

        if build:
            log.info(f"[{step.id}] podman build -t {img}:{tag} {build_ctx_path}")
            self._exec_srun(
                ["podman", "build", "-t", f"{img}:{tag}", f"{build_ctx_path}"], step
            )

        elif not self._config.skip_pull and not step.skip_pull:
            log.info(f"[{step.id}] podman pull {img}:{tag}")
            self._exec_srun(["podman", "pull", f"{img}:{tag}"], step)

        log.info(f"[{step.id}] podman create -t {img}:{tag} {cid}")
        self._exec_srun(self._create_cmd(step, f"{img}:{tag}", cid), step)

        self._spawned_containers.add(cid)

        log.info(f"[{step.id}] podman start --attach {cid}")
        ecode = self._exec_srun(
            ["podman", "start", "--attach", f"{cid}"], step, logging=True
        )

        self._spawned_containers.remove(cid)
        return ecode

    def _create_cmd(self, step, img, cid):
        container_args = self._get_container_kwargs(step, img, cid)

        if "volumes" not in container_args:
            container_args["volumes"] = []

        container_args.pop("detach")
        cmd = ["podman", "create"]
        cmd.extend(["--name", f"{container_args.pop('name')}"])
        cmd.extend(["--workdir", f"{container_args.pop('working_dir')}"])

        entrypoint = container_args.pop("entrypoint", None)
        if entrypoint:
            cmd.extend(["--entrypoint"])
            cmd.extend(entrypoint)

        # append volume and environment flags
        for vol in container_args.pop("volumes"):
            cmd.extend(["-v", f"{vol}"])
        for env_key, env_val in container_args.pop("environment").items():
            cmd.extend(["-e", f"{env_key}={env_val}"])

        command = container_args.pop("command")
        image = container_args.pop("image")

        # anything else is treated as a flag
        for k, v in container_args.items():
            flag = pu.key_value_to_flag(k, v)
            if flag:
                cmd.extend(flag)

        # append the image and the commands
        cmd.append(image)

        if command:
            cmd.extend(command)

        return cmd


class SingularityRunner(SlurmRunner, HostSingularityRunner):
    def __init__(self, **kw):
        super(SingularityRunner, self).__init__(init_spython_client=False, **kw)
        if self._config.reuse:
            log.fail("Reuse not supported for SingularityRunner.")

    def __exit__(self, exc_type, exc_value, exc_traceback):
        pass

    def run(self, step):
        self._setup_singularity_cache()
        cid = pu.sanitized_name(step.id, self._config.wid) + ".sif"
        self._container = cid

        build, img, _, _, build_ctx_path = self._get_build_info(step)

        if "shub://" in step.uses or "library://" in step.uses:
            build = False
            img = step.uses
            build_ctx_path = None

        self._exec_srun(["rm", "-rf", self._container], step)

        if build:
            recipefile = self._get_recipe_file(build_ctx_path, cid)
            log.info(f"[{step.id}] singularity build {self._container}")
            self._exec_srun(
                ["singularity", "build", "--fakeroot", self._container, recipefile],
                step,
            )
        else:
            log.info(f"[{step.id}] singularity pull {self._container}")
            self._exec_srun(["singularity", "pull", self._container, img], step)

        cmd = self._create_cmd(step, cid)
        self._spawned_containers.add(cid)

        if self._config.resman_opts.get(step.id, {}).get("mpi", True):
            ecode = self._exec_mpi(cmd, step)
        else:
            log.info(f'[{step.id}] {" ".join(cmd)}')
            ecode = self._exec_srun(cmd, step, logging=True)

        self._spawned_containers.remove(cid)
        return ecode

    def _create_cmd(self, step, cid):
        env = self._prepare_environment(step)
        for k, v in env.items():
            os.environ[k] = str(v)

        if step.runs:
            commands = step.runs
            cmd = ["singularity", "exec"]
        else:
            commands = step.args
            cmd = ["singularity", "run"]

        options = self._get_container_options()

        cmd.extend(options)
        cmd.extend([self._container])
        cmd.extend(commands)

        return cmd
