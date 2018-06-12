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
    help='Timeout limit for pipeline. Use s for seconds, m for minutes and h '
         'for hours. A single integer can also be used to specify timeout '
         'in seconds. Use double quotes if you wish to use more than one unit.'
         'For example: --timeout "2m 20s" will mean 140 seconds.',
    required=False,
    show_default=True,
    default="10800s"
)
@click.option(
    '--skip',
    help='Comma-separated list of stages to skip.',
    required=False,
)
@click.option(
    '--ignore-errors',
    is_flag=True,
    help='Execute all pipelines even if there is a failure, '
         'only when no pipeline argument is provided ',
    required=False,
)
@pass_context
def cli(ctx, pipeline, timeout, skip, ignore_errors):
    """Executes a pipeline and reports its status. When PIPELINE is given, it
    executes only the pipeline with such a name. If the argument is omitted,
    all pipelines are executed in lexicographical order. Reports an error if
    no pipelines have been configured.
    """
    cwd = os.getcwd()
    pipes = pu.read_config()['pipelines']
    project_root = pu.get_project_root()
    time_out = pu.parse_timeout(timeout)

    if len(pipes) == 0:
        pu.info("No pipelines defined in .popper.yml. "
                "Run popper init --help for more info.", fg='yellow')
        sys.exit(0)

    if pipeline:
        if ignore_errors:
            pu.warn("ignore-errors flag is ignored when pipeline "
                    "argument is provided")
        if pipeline not in pipes:
            pu.fail("Cannot find pipeline {} in .popper.yml".format(pipeline))
        status = run_pipeline(project_root, pipes[pipeline], time_out, skip)
    else:
        if os.path.basename(cwd) in pipes:
            # run just the one for CWD
            status = run_pipeline(project_root, pipes[os.path.basename(cwd)],
                                  time_out, skip)
        else:
            # run all
            for pipe in pipes:
                status = run_pipeline(
                    project_root, pipes[pipe], time_out, skip
                )

                if status == 'FAIL' and not ignore_errors:
                    break

    os.chdir(cwd)

    if status == 'FAIL':
        pu.fail("Failed to execute pipeline")


def run_pipeline(project_root, pipeline, timeout, skip):
    abs_path = os.path.join(project_root, pipeline['path'])

    pu.info("Executing " + os.path.basename(abs_path), fg='blue',
            bold=True, blink=True)

    os.chdir(abs_path)

    check_output('rm -rf popper_logs/ popper_status', shell=True)
    check_output('mkdir -p popper_logs/', shell=True)

    STATUS = "SUCCESS"

    with click.progressbar(pipeline['stages'], show_eta=False,
                           label="Current stage: ", item_show_func=str,
                           bar_template='[%(bar)s] %(label)s %(info)s',
                           show_percent=False) as stages:

        for stage in stages:

            stage_file = pu.get_filename(abs_path, stage)

            if skip:
                skipped = skip.split(',')
            else:
                skipped = []

            if not stage_file or stage in skipped:
                continue

            ecode = execute(stage_file, timeout, stages)

            if ecode != 0:
                pu.warn("Stage {} failed.".format(stage))
                STATUS = "FAIL"
                pu.warn("Logs for {}:".format(stage))
                for t in ['.err', '.out']:
                    logfile = 'popper_logs/{}{}'.format(stage_file, t)
                    with open(logfile, 'r') as f:
                        pu.warn("\n{}:\n{}".format(logfile, f.read()))

                # Execute teardown when some stage fails and then break
                teardown_file = pu.get_filename(abs_path, 'teardown')
                if (teardown_file and
                    stage != 'teardown' and
                    'teardown' in pipeline['stages'] and
                    'teardown' not in skipped):
                        execute(teardown_file, timeout)

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

    fg = 'green' if STATUS == "SUCCESS" else 'red'
    pu.info('status : ' + STATUS, fg=fg, bold=True)
    sys.stdout.write('\n')

    return STATUS


def execute(stage, timeout, bar=None):
    time_limit = time.time() + timeout
    sleep_time = 1
    out_fname = 'popper_logs/{}.{}'.format(stage, 'out')
    err_fname = 'popper_logs/{}.{}'.format(stage, 'err')

    with open(out_fname, "wb") as outf, open(err_fname, "wb") as errf:
        p = subprocess.Popen('./' + stage, shell=True, stdout=outf,
                             stderr=errf, preexec_fn=os.setsid)

        if not bar:
            pu.info("Running: {}".format(stage))

        while p.poll() is None:

            if time.time() > time_limit:
                os.killpg(os.getpgid(p.pid), signal.SIGTERM)
                sys.stdout.write(' time out!')
                break

            if sleep_time < 300:
                sleep_time *= 2

            if bar:
                for i in range(sleep_time):
                    bar.label = bar.label + '\b_'
                    bar.render_progress()
                    time.sleep(0.5)
                    bar.label = bar.label + '\b '
                    bar.render_progress()
                    time.sleep(0.5)

    return p.poll()


class Unbuffered(object):
    def __init__(self, stream):
        self.stream = stream

    def write(self, data):
        self.stream.write(data)
        self.stream.flush()

    def __getattr__(self, attr):
        return getattr(self.stream, attr)
