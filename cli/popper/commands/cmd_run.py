#!/usr/bin/env python

import click
import os
import popper.utils as pu
import subprocess
import time
import signal
import sys

from popper.cli import pass_context
from subprocess import check_output


@click.command('run', short_help='Run pipeline and report on its status.')
@click.argument('pipeline', required=False)
@click.option(
    '--timeout',
    help='Timeout limit for pipeline in seconds.',
    required=False,
    show_default=True,
    default=10800
)
@click.option(
    '--skip',
    help='Comma-separated list of stages to skip.',
    required=False,
)
@pass_context
def cli(ctx, pipeline, timeout, skip):
    """Executes a pipeline and reports its status. When PIPELINE is given, it
    executes only the pipeline with such a name. If the argument is omitted,
    all pipelines are executed in lexicographical order.
    """
    cwd = os.getcwd()
    pipes = pu.read_config()['pipelines']
    project_root = pu.get_project_root()

    if pipeline:
        if pipeline not in pipes:
            pu.fail("Cannot find pipeline {} in .popper.yml".format(pipeline))
        status = run_pipeline(project_root, pipes[pipeline], timeout, skip)
    else:
        if os.path.basename(cwd) in pipes:
            # run just the one for CWD
            status = run_pipeline(project_root, pipes[os.path.basename(cwd)],
                                  timeout, skip)
        else:
            # run all
            for pipe in pipes:
                status = run_pipeline(project_root, pipes[pipe], timeout, skip)

                if status == 'FAIL':
                    break

    os.chdir(cwd)

    if status == 'FAIL':
        pu.fail("Failed to execute pipeline")


def run_pipeline(project_root, pipeline, timeout, skip):
    abs_path = os.path.join(project_root, pipeline['path'])

    pu.info("Executing " + os.path.basename(abs_path))

    os.chdir(abs_path)

    check_output('rm -rf popper_logs/ popper_status', shell=True)
    check_output('mkdir -p popper_logs/', shell=True)

    STATUS = "SUCCESS"

    for stage in pipeline['stages']:

        if os.path.isfile(stage):
            stage_file = stage
        elif os.path.isfile(stage + '.sh'):
            stage_file = stage + '.sh'
        else:
            continue

        if skip and stage in skip.split(','):
            continue

        ecode = execute(stage_file, timeout)

        if ecode != 0:
            pu.info("Stage {} failed.".format(stage))
            STATUS = "FAIL"
            pu.info("Logs for {}:.".format(stage))
            for t in ['.err', '.out']:
                with open('popper_logs/{}{}'.format(stage, t), 'r') as f:
                    pu.info(f.read())
            break

        if 'valid' in stage:
            STATUS = "GOLD"
            with open('popper_logs/validate.sh.out', 'r') as f:
                validate_output = f.readlines()
                if len(validate_output) == 0:
                    STATUS = "SUCCESS"
                for line in validate_output:
                    if '[true]' not in line:
                        STATUS = "SUCCESS"

    with open('popper_status', 'w') as f:
        f.write(STATUS + '\n')

    pu.info('status: ' + STATUS)

    return STATUS


def execute(stage, timeout):
    time_limit = time.time() + timeout
    sleep_time = 1
    out_fname = 'popper_logs/{}.{}'.format(stage, 'out')
    err_fname = 'popper_logs/{}.{}'.format(stage, 'err')

    sys.stdout.write(stage + ' ')

    with open(out_fname, "wb") as outf, open(err_fname, "wb") as errf:
        p = subprocess.Popen('./' + stage, shell=True, stdout=outf,
                             stderr=errf, preexec_fn=os.setsid)

        while p.poll() is None:
            sys.stdout.write('.')

            if time.time() > time_limit:
                os.killpg(os.getpgid(p.pid), signal.SIGTERM)
                sys.stdout.write(' time out!')
                break

            if sleep_time < 300:
                sleep_time *= 2

            time.sleep(sleep_time)

    sys.stdout.write('\n')

    return p.poll()


class Unbuffered(object):
    def __init__(self, stream):
        self.stream = stream

    def write(self, data):
        self.stream.write(data)
        self.stream.flush()

    def __getattr__(self, attr):
        return getattr(self.stream, attr)
