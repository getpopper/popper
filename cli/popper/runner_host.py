import os

from subprocess import CalledProcessError, PIPE, Popen, STDOUT

from popper import utils as pu
from popper.cli import log as log
from popper.runner import StepRunner as StepRunner

host_running_processes = []


class HostRunner(StepRunner):
    """Run an step on the Host Machine."""

    def __init__(self, config):
        super(HostRunner, self).__init__(config)
        if self.config.reuse:
            log.warning('Reuse not supported for HostRunner.')

    def run(self, step):
        curr_env = os.environ
        os.environ = StepRunner.prepare_environment(step, curr_env)

        cmd = step.get('runs', [])
        if not cmd:
            raise AttributeError(f"Expecting 'runs' attribute in step.")
        cmd.extend(step.get('args', []))

        log.info(f'[{step["name"]}] {" ".join(cmd)}')

        if self.config.dry_run:
            StepRunner.handle_exit(step, 0)

        with Popen(' '.join(cmd), stdout=PIPE, stderr=STDOUT,
                   shell=True, universal_newlines=True,
                   preexec_fn=os.setsid) as p:
            try:
                global host_running_processes
                host_running_processes.append(p.pid)

                log.debug('Reading process output')

                for line in iter(p.stdout.readline, ''):
                    line_decoded = pu.decode(line)
                    log.step_info(line_decoded[:-1])

                p.wait()
                ecode = p.poll()
                log.debug('Code returned by process: {}'.format(ecode))

            except CalledProcessError as ex:
                msg = "Command '{}' failed: {}".format(cmd, ex)
                ecode = ex.returncode
                log.step_info(msg)
            finally:
                log.step_info()

        os.environ = curr_env
        StepRunner.handle_exit(step, ecode)
