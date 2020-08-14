import os
import time
import signal
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
        self._ctx_prepared = False

    def __exit__(self, exc_type, exc, traceback):
        self._spawned_jobs = set()

    def _get_base_srun_cmd(self):
        return [
            "srun", "-N", f"{self._config.resman_opts.N}", "--nodelist", self._config.resman_opts.nodelist, "--ntasks", f"{self._config.resman_opts.N}", "--ntasks-per-node", "1" 
        ]

    def _prepare_ctx(self):
        log.debug(self._config.workspace_dir)
        for node in self._config.resman_opts.nodelist.split(","):
            cmd = ["scp", "-r", self._config.workspace_dir, f"{node}:{os.path.dirname(self._config.workspace_dir)}"]
            log.debug(cmd)
            HostRunner._exec_cmd(cmd)

    def _exec_srun(self, cmd, logging=True):
        if not self._ctx_prepared:
            self._prepare_ctx()
            self._ctx_prepared = True

        _cmd = self._get_base_srun_cmd()
        _cmd.extend(cmd)
        log.debug(f"Command: {_cmd}")

        if self._config.dry_run:
            return 0

        _, ecode, _ = HostRunner._exec_cmd(_cmd, logging=logging)
        return ecode


class DockerRunner(SlurmRunner, HostDockerRunner):
    def __init__(self, **kw):
        super(DockerRunner, self).__init__(init_docker_client=False, **kw)

    def __exit__(self, exc_type, exc, traceback):
        pass

    def run(self, step):
        """Execute the given step via slurm in the docker engine."""
        cid = pu.sanitized_name(step.id, self._config.wid)

        build, _, img, tag, build_ctx_path = self._get_build_info(step)

        self._exec_srun(["docker", "rm", "-f", f"{cid}"])

        if build:
            log.info(f'[{step.id}] docker build -t {img}:{tag} {build_ctx_path}')
            self._exec_srun(["docker", "build", "-t", f"{img}:{tag}", f"{build_ctx_path}"])

        elif not self._config.skip_pull and not step.skip_pull:
            log.info(f'[{step.id}] docker pull {img}:{tag}')
            self._exec_srun(["docker", "pull", f"{img}:{tag}"])

        log.info(f'[{step.id}] docker create -t {img}:{tag} {cid}')
        self._exec_srun(self._create_cmd(step, f"{img}:{tag}", cid))

        self._spawned_containers.add(cid)

        log.info(f'[{step.id}] docker start --attach {cid}')
        ecode = self._exec_srun(["docker", "start", "--attach", f"{cid}"], logging=True)
        
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

        self._exec_srun(["podman", "rm", "-f", f"{cid}"])

        if build:
            log.info(f'[{step.id}] podman build -t {img}:{tag} {build_ctx_path}')
            self._exec_srun(["podman", "build", "-t", f"{img}:{tag}", f"{build_ctx_path}"])

        elif not self._config.skip_pull and not step.skip_pull:
            log.info(f'[{step.id}] podman pull {img}:{tag}')
            self._exec_srun(["podman", "pull", f"{img}:{tag}"])

        log.info(f'[{step.id}] podman create -t {img}:{tag} {cid}')
        self._exec_srun(self._create_cmd(step, f"{img}:{tag}", cid))

        self._spawned_containers.add(cid)

        log.info(f'[{step.id}] podman start --attach {cid}')
        ecode = self._exec_srun(["podman", "start", "--attach", f"{cid}"], logging=True)
        
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

        self._exec_srun(["rm", "-rf", self._container])

        if build:
            recipefile = self._get_recipe_file(build_ctx_path, cid)
            log.info(f'[{step.id}] singularity build {self._container}')
            self._exec_srun(
                ["singularity", "build", "--fakeroot", self._container, recipefile]
            )
        else:
            log.info(f'[{step.id}] singularity pull {self._container}')
            self._exec_srun(["singularity", "pull", self._container, img])

        cmd = self._create_cmd(step, cid)
        self._spawned_containers.add(cid)
        log.info(f'[{step.id}] singularity run/exec {self._container} {cmd}')
        ecode = self._exec_srun(cmd, logging=True)
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
