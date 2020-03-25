import os
from subprocess import PIPE, Popen, STDOUT, SubprocessError

import docker

from popper import utils as pu
from popper import scm
from popper.cli import log as log
from popper.runner import StepRunner as StepRunner
from popper.runner_host import DockerRunner as HostDockerRunner
from popper.runner_host import HostRunner


class SlurmRunner(StepRunner):

    spawned_processes = set()

    def __init__(self, config):
        super(SlurmRunner, self).__init__(config)

    def __exit__(self, exc_type, exc, traceback):
        SlurmRunner.spawned_processes = set()

    def exec_srun_cmd(self, cmd, env=None):
        srun_cmd = ['srun']

        options = self.config.resman_options
        if options:
            if options.get(self.step['name']):
                step_slurm_config = options[self.step['name']]
                for k, v in step_slurm_config.items():
                    if isinstance(v, bool):
                        srun_cmd.append(f"--{k}")
                    else:
                        srun_cmd.append(f"--{k}")
                        srun_cmd.append(f"{v}")

        # join the srun prefix
        cmd = [*srun_cmd, *cmd]
        log.debug(cmd)

        ecode = pu.exec_cmd(
            cmd, env, self.config.workspace_dir, SlurmRunner.spawned_processes)
        return ecode

    def stop_srun_cmd(self):
        for p in SlurmRunner.spawned_processes:
            log.info(f'Stopping proces {p.pid}')
            p.kill()


class DockerRunner(SlurmRunner, HostDockerRunner):
    """Runs steps in docker."""

    def __init__(self, config):
        super(DockerRunner, self).__init__(config)

    def run(self, step):
        """Execute the given step in docker."""
        self.step = step
        cid = pu.sanitized_name(step['name'], self.config.wid)

        container = HostDockerRunner.find_container(cid)

        if container and not self.config.reuse and not self.config.dry_run:
            container.remove(force=True)

        container = HostDockerRunner.create_container(cid, step, self.config)
        log.info(f'[{step["name"]}] srun docker start')

        if self.config.dry_run:
            return 0

        HostDockerRunner.spawned_containers.append(container)
        ecode = self.start_container(cid)
        return ecode

    def start_container(self, cid):
        docker_cmd = f"docker start --attach {cid}"
        ecode = self.exec_srun_cmd(docker_cmd.split(" "))
        return ecode

    def stop_running_tasks(self):
        for c in HostDockerRunner.spawned_containers:
            log.info(f'Stopping container {c.name}')
            c.stop()
        self.stop_srun_cmd()
