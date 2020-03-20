import os
from subprocess import PIPE, Popen, STDOUT, SubprocessError

import docker

from popper import utils as pu
from popper import scm
from popper.cli import log as log
from popper.runner import StepRunner as StepRunner
from popper.runner_host import DockerRunner as HostDockerRunner


class SlurmRunner(StepRunner):

    spawned_processes = []

    def __init__(self, config):
        super(SlurmRunner, self).__init__(config)

    def __exit__(self, exc_type, exc, traceback):
        SlurmRunner.spawned_processes = []

    def exec_srun_cmd(self, cmd):
        step_env = SlurmRunner.prepare_environment(self.step, os.environ)
        try:
            cmd.insert(0, 'srun')
            with Popen(cmd, stdout=PIPE, stderr=STDOUT,
                       universal_newlines=True, preexec_fn=os.setsid,
                       env=step_env, cwd=self.config.workspace_dir) as p:
                SlurmRunner.spawned_processes.append(p)

                log.debug('Reading process output')

                for line in iter(p.stdout.readline, ''):
                    line_decoded = pu.decode(line)
                    log.step_info(line_decoded[:-1])

                p.wait()
                ecode = p.poll()

            log.debug(f'Code returned by process: {ecode}')

        except SubprocessError as ex:
            ecode = ex.returncode
            log.step_info(f"Command '{cmd[0]}' failed with: {ex}")
        except Exception as ex:
            ecode = 1
            log.step_info(f"Command raised non-SubprocessError error: {ex}")

        return ecode

    def stop_srun_cmd(self):
        for p in SlurmRunner.spawned_processes:
            log.info(f'Stopping proces {p.pid}')
            p.kill()


class HostRunner(SlurmRunner):

    def __init__(self, config):
        super(HostRunner, self).__init__(config)
        if self.config.reuse:
            log.warning('Reuse not supported for HostRunner.')

    def run(self, step):
        self.step = step
        cmd = step.get('runs', [])
        if not cmd:
            raise AttributeError(f"Expecting 'runs' attribute in step.")
        cmd.extend(step.get('args', []))

        log.info(f'[{step["name"]}] {cmd}')

        if self.config.dry_run:
            return 0

        log.debug(f'Environment:\n{pu.prettystr(os.environ)}')

        ecode = self.exec_srun_cmd(cmd)
        return ecode

    def stop_running_tasks(self):
        self.stop_srun_cmd()


class DockerRunner(SlurmRunner, HostDockerRunner):
    """Runs steps in docker."""

    def __init__(self, config):
        super(DockerRunner, self).__init__(config)

    def run(self, step):
        """Execute the given step in docker."""
        self.step = step
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

        log.info(f'[{step["name"]}] docker start')

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
