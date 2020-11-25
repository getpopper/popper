import os
import time
import signal
import socket
import threading

from popper import utils as pu
from popper.cli import log as log
from popper.runner_host import HostRunner
from popper.runner_host import SingularityRunner as HostSingularityRunner


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
        self._nodes = self._config.resman_opts.get(step.id, {}).get("nodes", 1)
        self._nodelist = self._config.resman_opts.get(step.id, {}).get("nodelist", None)
        self._ntasks = self._config.resman_opts.get(step.id, {}).get(
            "ntasks", self._nodes
        )
        self._ntasks_per_node = self._config.resman_opts.get(step.id, {}).get(
            "ntasks-per-node", 1
        )

    def _get_resman_kwargs(self, step):
        default_options = ["nodes", "nodelist", "ntasks", "ntasks-per-node"]
        resman_options = []
        for k, v in self._config.resman_opts.get(step.id, {}).items():
            if k not in default_options:
                flag = pu.key_value_to_flag(k, v)
                if flag:
                    resman_options.extend(flag.split())

        return resman_options

    def _exec_srun(self, cmd, step, **kwargs):
        self._set_config_vars(step)
        _cmd = [
            "srun",
            "--nodes",
            f"{self._nodes}",
            "--ntasks",
            f"{self._ntasks}",
            "--ntasks-per-node",
            f"{self._ntasks_per_node}",
        ]

        if self._nodelist:
            _cmd.extend(["--nodelist", self._nodelist])

        _cmd.extend(self._get_resman_kwargs(step))
        _cmd.extend(cmd)

        log.debug(f"Command: {_cmd}")

        if self._config.dry_run:
            return 0

        _, ecode, _ = HostRunner._exec_cmd(_cmd, **kwargs)
        return ecode

    def _exec_mpi(self, cmd, step, **kwargs):
        self._set_config_vars(step)
        job_name = pu.sanitized_name(step.id, self._config.wid)
        mpi_cmd = ["mpirun", f"{' '.join(cmd)}"]

        job_script = os.path.join(f"{job_name}.sh")
        out_file = os.path.join(f"{job_name}.out")

        with open(out_file, "w"):
            pass

        with open(job_script, "w") as f:
            f.write("#!/bin/bash\n")
            f.write(f"#SBATCH --job-name={job_name}\n")
            f.write(f"#SBATCH --output={out_file}\n")
            f.write(f"#SBATCH --nodes={self._nodes}\n")
            f.write(f"#SBATCH --ntasks={self._ntasks}\n")
            f.write(f"#SBATCH --ntasks-per-node={self._ntasks_per_node}\n")
            if self._nodelist:
                f.write(f"#SBATCH --nodelist={self._nodelist}\n")
            f.write(" ".join(mpi_cmd))

        sbatch_cmd = [
            "sbatch",
            "--wait",
        ]
        sbatch_cmd.extend(self._get_resman_kwargs(step))
        sbatch_cmd.extend([job_script])

        log.debug(f"Command: {sbatch_cmd}")

        if self._config.dry_run:
            return 0

        self._spawned_jobs.add(job_name)
        self._start_out_stream(out_file)

        _, ecode, _ = HostRunner._exec_cmd(sbatch_cmd, **kwargs)

        self._stop_out_stream()
        self._spawned_jobs.remove(job_name)

        return ecode

    def stop_running_tasks(self):
        for job_name in self._spawned_jobs:
            log.info(f"Cancelling job {job_name}")
            _, ecode, _ = HostRunner._exec_cmd(["scancel", "--name", job_name])
            if ecode != 0:
                log.warning(f"Failed to cancel the job {job_name}.")


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
        self._container = os.path.join(self._singularity_cache, cid)

        build, img, _, _, build_ctx_path = self._get_build_info(step)

        if "shub://" in step.uses or "library://" in step.uses:
            build = False
            img = step.uses
            build_ctx_path = None

        self._exec_srun(["rm", "-rf", self._container], step)

        if build:
            recipefile = self._get_recipe_file(build_ctx_path, cid)
            log.info(f"[{step.id}] srun singularity build {self._container}")
            self._exec_srun(
                ["singularity", "build", "--fakeroot", self._container, recipefile,],
                step,
                cwd=os.path.dirname(recipefile),
            )
        else:
            log.info(f"[{step.id}] srun singularity pull {self._container}")
            self._exec_srun(["singularity", "pull", self._container, img], step)

        cmd = self._create_cmd(step, cid)
        self._spawned_containers.add(cid)

        if self._config.resman_opts.get(step.id, {}).get("mpi", True):
            log.info(f'[{step.id}] sbatch {" ".join(cmd)}')
            ecode = self._exec_mpi(cmd, step)
        else:
            log.info(f'[{step.id}] srun {" ".join(cmd)}')
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
