import os

from subprocess import PIPE, Popen, STDOUT, SubprocessError

from popper import utils as pu
from popper.cli import log as log
from popper.runner import StepRunner as StepRunner



class HostRunner(StepRunner):
    """Run an step on the Host Machine."""

    spawned_processes = []

    def __init__(self, config):
        super(HostRunner, self).__init__(config)
        if self.config.reuse:
            log.warning('Reuse not supported for HostRunner.')

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        pass

    def run(self, step):
        step_env = StepRunner.prepare_environment(step, os.environ)

        cmd = step.get('runs', [])
        if not cmd:
            raise AttributeError(f"Expecting 'runs' attribute in step.")
        cmd.extend(step.get('args', []))

        log.info(f'[{step["name"]}] {cmd}')

        if self.config.dry_run:
            return 0

        log.debug(f'Environment:\n{pu.prettystr(os.environ)}')

        try:
            with Popen(cmd, stdout=PIPE, stderr=STDOUT,
                       universal_newlines=True, preexec_fn=os.setsid,
                       env=step_env, cwd=self.config.workspace_dir) as p:
                HostRunner.spawned_processes.append(p)

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

    def stop_running_tasks(self):
        for p in HostRunner.spawned_processes:
            log.info(f'Stopping proces {p.pid}')
            p.kill()
