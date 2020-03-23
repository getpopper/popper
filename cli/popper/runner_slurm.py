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

    spawned_processes = []

    def __init__(self, config):
        super(SlurmRunner, self).__init__(config)

    def __exit__(self, exc_type, exc, traceback):
        SlurmRunner.spawned_processes = []

    def exec_srun_cmd(self, cmd, env=None):
        cmd.insert(0, 'srun')
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
        cid = pu.sanitized_name(step['name'], self.config.wid)

        build, img, dockerfile = HostDockerRunner.get_build_info(
            step, self.config.workspace_dir, self.config.workspace_sha)

        container = HostDockerRunner.find_container(cid)

        if container and not self.config.reuse and not self.config.dry_run:
            container.remove(force=True)

        # build or pull
        if build:
            HostDockerRunner.docker_build(step, img, dockerfile,
                                          self.config.dry_run)
        elif not self.config.skip_pull and not step.get('skip_pull', False):
            HostDockerRunner.docker_pull(step, img, self.config.dry_run)

        msg = f'{img} {step.get("runs", "")} {step.get("args", "")}'
        log.info(f'[{step["name"]}] docker create {msg}')

        if not self.config.dry_run:
            engine_config = {
                "image": img,
                "command": step.get('args', None),
                "name": cid,
                "volumes": [
                    f'{self.config.workspace_dir}:/workspace',
                    '/var/run/docker.sock:/var/run/docker.sock'
                ],
                "working_dir": '/workspace',
                "environment": SlurmRunner.prepare_environment(step),
                "entrypoint": step.get('runs', None),
                "detach": True
            }

            if self.config.engine_options:
                HostDockerRunner.update_engine_config(
                    engine_config, self.config.engine_options)
            log.debug(f'Engine configuration: {pu.prettystr(engine_config)}\n')

            container = HostDockerRunner.d.containers.create(**engine_config)

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
