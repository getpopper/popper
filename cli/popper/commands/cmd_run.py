#!/usr/bin/env python
import click
import os
import popper.utils as pu
import subprocess
import time
import signal
import sys
import re
import requests

from popper.cli import pass_context
from subprocess import check_output
from collections import defaultdict


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
    help='Comma-separated list of stages to skip when a pipeline is'
         'specifier, otherwise a comma-separated list of pipelines to skip.',
    required=False,
)
@click.option(
    '--ignore-errors',
    is_flag=True,
    help='Execute all pipelines even if there is a failure, '
         'only when no pipeline argument is provided ',
    required=False,
)
@click.option(
    '--volume',
    is_flag=True,
    help="Volume available to the pipeline. Can be given "
         "multiple times. This flag is ignored when the "
         "environment is 'host'.",
    required=False,
)
@click.option(
    '--environment',
    is_flag=True,
    help="Environment variable available to the pipeline. "
         "Can be given multiple times. "
         "This flag is ignored when the environment is 'host'.",
    required=False,
)
@pass_context
def cli(ctx, pipeline, timeout, skip, volume, environment, ignore_errors):
    """Executes a pipeline and reports its status. When PIPELINE is given, it
    executes only the pipeline with such a name. If the argument is omitted,
    all pipelines are executed in lexicographical order. Reports an error if
    no pipelines have been configured.
    """
    cwd = os.getcwd()
    pipes = pu.read_config()['pipelines']

    project_root = pu.get_project_root()

    if len(pipes) == 0:
        pu.info("No pipelines defined in .popper.yml. "
                "Run popper init --help for more info.", fg='yellow')
        sys.exit(0)

    if os.environ.get('CI', False):
        args = ['git', 'log', '-1', '--pretty=%B']

        p = subprocess.Popen(args, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        output, error = p.communicate()

        if p.returncode == 0:
            try:
                commit = output.decode()  # Python 3 returns bytes
            except AttributeError:
                commit = output
        else:
            commit = ""

        # Check for pull requests
        if "Merge" in commit:

            pu.info("merge detected.")
            commit_id = re.search('Merge (.+?) into', commit).group(1)

            args = ['git', 'show', '-s', '--format=%B', commit_id]

            p = subprocess.Popen(args, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
            output, error = p.communicate()

            if p.returncode == 0:
                try:
                    commit = output.decode()  # Python 3  returns bytes
                except AttributeError:
                    commit = output
            else:
                commit = ""

        if "popper:skip" in commit:
            pu.info("popper:skip flag detected. "
                    "Skipping execution of commit")
            sys.exit(0)

        if "popper:whitelist" in commit:
            pu.info("popper:whitelist flag detected.")
            try:
                # Checks if the last commit message has the flag
                # `popper:whitelist[pipeline]` and gets the pipeline.
                pipeline = re.search('popper:whitelist\[(.+?)\]',
                                     commit).group(1)
                pu.info("Executing popper:whitelist[{}]"
                        .format(pipeline))
            except AttributeError:
                pipeline = None
                pu.warn("Couldn't find pipeline associated with the "
                        "popper:whitelist flag. "
                        "Assigning pipeline to None")

    if pipeline:
        if ignore_errors:
            pu.warn("--ignore-errors flag is ignored when pipeline "
                    "argument is provided")
        if pipeline not in pipes:
            pu.fail("Cannot find pipeline {} in .popper.yml".format(pipeline))
        skipped = skip.split(',') if skip is not None else []
        status = run_pipeline(project_root, pipes[pipeline], timeout, skipped, volume, environment)
    else:
        if os.path.basename(cwd) in pipes:
            # run just the one for CWD
            skipped = skip.split(',') if skip is not None else []
            status = run_pipeline(project_root, pipes[os.path.basename(cwd)],
                                  timeout, skipped, volume, environment)
        else:
            # run all
            skip_list = skip.split(',') if skip else []

            skipped_stages = defaultdict(list)
            for skip in skip_list:
                pair = skip.split(':')
                if len(pair) == 2:
                    pipe, stage = pair
                    skipped_stages[pipe].append(stage)

            for pipe in pipes:
                if pipe not in skip_list:
                    status = run_pipeline(
                        project_root,
                        pipes[pipe],
                        timeout,
                        skipped_stages[pipe],
                        volume,
                        environment
                    )

                    if status == 'FAIL' and not ignore_errors:
                        break

    os.chdir(cwd)

    remote_url = pu.get_remote_url()

    if remote_url and os.environ.get('CI', False):
        baseurl = pu.read_config().get(
            'badge-server-url', 'http://badges.falsifiable.us'
        )
        org, repo = remote_url.split('/')[-2:]
        badge_server_url = '{}/{}/{}'.format(baseurl, org, repo)
        try:
            commit_id = check_output(['git', 'rev-parse', 'HEAD'])[:-1]
            data = {
                'timestamp': int(time.time()),
                'commit_id': commit_id,
                'status': status
            }
            try:
                r = requests.post(badge_server_url, data=data)
                if r.status_code != 201:
                    pu.warn("Could not create a record on the badge server")
            except requests.exceptions.RequestException:
                pu.warn("Could not communicate with the badge server")
        except subprocess.CalledProcessError:
            pu.warn("No commit log found")

    if status == 'FAIL':
        pu.fail("Failed to execute pipeline")


def run_in_docker(envs, abs_path, skipped, timeout, volumes, environments):
    pu.info("Executing in Docker...", fg='blue',
            bold=True, blink=True)

    docker_flags = ""

    if environments:
        for environment in environments:
            docker_flags += "-e " + environment + " "

    if volumes:
        for volume in volumes:
            docker_flags += "-v " + volume + " "

    popper_flags = ""

    if skipped:
        popper_flags += "--skip=" + skipped + " "

    cmd_args = " run --rm -i " + docker_flags

    cmd_args += " --volume " + abs_path + ":" + abs_path + " --workdir " + abs_path + " --volume " \
                + " /var/run/docker.sock:/var/run/docker.sock " + " falsifiable/poppercheck:"

    status = []

    for env in envs:
        try:
            output = ""
            output = check_output("docker " + cmd_args + env + " " + popper_flags, shell=True)
        except Exception:
            pu.warn("Please make sure you're using a valid docker image.\n"
                    "You can check the available docker images here:\n"
                    "https://hub.docker.com/r/falsifiable/poppercheck/tags/")

        try:
            status.append(re.search('status: (.+?)\n',
                                    output).group(1))
        except Exception:
            status.append("FAIL")

        if status[-1] == "SUCCESS":
            fg = 'green'
        elif status[-1] == "GOLD":
            fg = 'yellow'
        else:
            fg = 'red'
        pu.info("Environment " + env + ":\n" + "status: {}\n".format(status[-1]), fg=fg, bold=True)

    # Checks if all status are the same.
    if status.count(status[0]) == len(status):
        STATUS = status[0]
    else:
        STATUS = "FAIL"

    return STATUS


def run_on_host(pipeline, abs_path, skipped, timeout):
    pu.info("Executing on host...", fg='blue',
            bold=True, blink=True)

    status = "SUCCESS"

    with click.progressbar(pipeline['stages'], show_eta=False,
                           item_show_func=str,
                           bar_template='[%(bar)s] %(info)s',
                           show_percent=False) as stages:

        for stage in stages:

            stage_file = pu.get_filename(abs_path, stage)

            if not stage_file or stage in skipped:
                continue

            ecode = execute(stage_file, timeout, stages)

            if ecode != 0:
                pu.info("\n\nStage '{}' failed.".format(stage))
                status = "FAIL"
                for t in ['.err', '.out']:
                    logfile = 'popper_logs/{}{}'.format(stage_file, t)
                    with open(logfile, 'r') as f:
                        pu.info("\n" + t + ":\n", bold=True, fg='red')
                        pu.info(f.read())

                # Execute teardown when some stage fails and then break
                teardown_file = pu.get_filename(abs_path, 'teardown')
                if (teardown_file and
                        stage != 'teardown' and
                        'teardown' in pipeline['stages'] and
                        'teardown' not in skipped):
                    execute(teardown_file, timeout)

                break

            if 'valid' in stage:
                status = "GOLD"
                with open('popper_logs/validate.sh.out', 'r') as f:
                    validate_output = f.readlines()
                    if len(validate_output) == 0:
                        status = "SUCCESS"
                    for line in validate_output:
                        if '[true]' not in line:
                            status = "SUCCESS"
    return status


def run_pipeline(project_root, pipeline, time_out, skipped, volume, environment):

    timeout = pu.parse_timeout(time_out)

    abs_path = os.path.join(project_root, pipeline['path'])

    pu.info("Executing " + os.path.basename(abs_path), fg='blue',
            bold=True, blink=True)

    os.chdir(abs_path)

    check_output('rm -rf popper_logs/ popper_status', shell=True)
    check_output('mkdir -p popper_logs/', shell=True)

    envs = pipeline['envs']

    status = "SUCCESS"

    if len(envs) == 0:
        pu.warn("No environment in .popper.yml, using host")
        envs = ["host"]

    if "host" in envs:
        status = run_on_host(pipeline, abs_path, skipped, timeout)
        envs.remove("host")

    status_copy = status

    if len(envs) > 0:
        status = run_in_docker(envs, abs_path, skipped, time_out, volume, environment)

    if status_copy != status:
        status = "FAIL"

    with open('popper_status', 'w') as f:
        f.write(status + '\n')

    if status == "SUCCESS":
        fg = 'green'
    elif status == "GOLD":
        fg = 'yellow'
    else:
        fg = 'red'
    pu.info('\nstatus: {}\n'.format(status), fg=fg, bold=True)

    return status


def execute(stage, timeout, bar=None):
    time_limit = time.time() + timeout
    sleep_time = 1
    out_fname = 'popper_logs/{}.{}'.format(stage, 'out')
    err_fname = 'popper_logs/{}.{}'.format(stage, 'err')

    with open(out_fname, "wb") as outf, open(err_fname, "wb") as errf:
        p = subprocess.Popen('./' + stage, shell=True, stdout=outf,
                             stderr=errf, preexec_fn=os.setsid)

        if os.environ.get('CI', False):
            # print info when in CI environment
            print('')
            pu.info("Running: {}".format(stage))

        while p.poll() is None:

            if time.time() > time_limit:
                os.killpg(os.getpgid(p.pid), signal.SIGTERM)
                sys.stdout.write(' time out!')
                break

            if sleep_time < 300:
                sleep_time *= 2

            if os.environ.get('CI', False):
                # print dot every 10 secs when in CI environment
                for i in range(sleep_time):
                    if i % 10 == 0:
                        sys.stdout.write('.')
                time.sleep(sleep_time)
                continue

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
