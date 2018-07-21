#!/usr/bin/env python

import click
import copy
import os
import popper.utils as pu
import signal
import subprocess
import time
import sys
import re
import requests

from popper.cli import pass_context
from subprocess import check_output


@click.command('run',
               short_help='Run one or more pipelines and report on their '
                          'status.')
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
    '--output',
    help='Directory where logs are stored, relative to pipeline folder.',
    required=False,
    show_default=True,
    default="popper/"
)
@click.option(
    '--skip',
    help="Comma-separated list of stages to skip. Only works when a single"
         "pipeline is being executed.",
    required=False,
)
@click.option(
    '--ignore-errors',
    help='Execute all pipelines even if there is a failure.',
    is_flag=True,
    required=False,
)
@click.option(
    '--no-badge-update',
    help='Do not update the status of the pipeline against the badge server.',
    is_flag=True,
    required=False,
)
@pass_context
def cli(ctx, pipeline, timeout, skip, ignore_errors, output,
        no_badge_update):
    """Executes one or more pipelines and reports on their status. When
    PIPELINE is given, it executes only the pipeline with that name. If the
    argument is omitted, all pipelines are executed in lexicographical order.
    """
    project_pipelines = pu.read_config()['pipelines']

    if len(project_pipelines) == 0:
        pu.info("No pipelines defined in .popper.yml. "
                "Run popper init --help for more info.", fg='yellow')
        sys.exit(0)

    project_root = pu.get_project_root()

    cwd = os.getcwd()

    pipelines = get_pipelines_to_execute(cwd, pipeline, project_pipelines)

    if os.environ.get('CI', False):
        pipes_from_log = pipelines_from_commit_message(project_pipelines)
        if len(pipes_from_log) != 0:
            pu.info("Found 'CI', ignoring PIPELINE argument.")
            pipelines = pipes_from_log

    for pipe_n, pipe_d in pipelines.items():
        for env in pipe_d.get('envs', ['host']):
            status = run_pipeline(project_root, pipe_n, pipe_d, env, timeout,
                                  skip, ignore_errors, output)
            if status == 'FAIL' and not ignore_errors:
                break

    os.chdir(cwd)

    if os.environ.get('CI', False) and not no_badge_update:
        update_badge(status)

    if status == 'FAIL':
        pu.fail("Failed to execute pipeline")


def get_pipelines_to_execute(cwd, pipe_n, project_pipelines):
    pipelines = {}
    if pipe_n:
        if pipe_n not in project_pipelines:
            pu.fail("Pipeline '{}' not in .popper.yml".format(pipe_n))
        return {pipe_n: project_pipelines[pipe_n]}
    else:
        cwd_pipe_n = os.path.basename(cwd)
        if cwd_pipe_n in project_pipelines:
            pipelines = {cwd_pipe_n: project_pipelines[cwd_pipe_n]}
        else:
            pipelines = project_pipelines

    return pipelines


def update_badge(status):
    if pu.is_repo_empty():
        pu.warn('No commit log found')

    remote_url = pu.get_remote_url()

    if remote_url:
        baseurl = pu.read_config().get(
            'badge-server-url', 'http://badges.falsifiable.us'
        )
        org, repo = remote_url.split('/')[-2:]
        badge_server_url = '{}/{}/{}'.format(baseurl, org, repo)
        data = {
            'timestamp': int(time.time()),
            'commit_id': pu.get_head_commit(),
            'status': status
        }
        try:
            r = requests.post(badge_server_url, data=data)
            if r.status_code != 201:
                pu.warn("Could not create a record on the badge server")
        except requests.exceptions.RequestException:
            pu.warn("Could not communicate with the badge server")


def pipelines_from_commit_message(project_pipelines):

    # check if repo is empty
    if pu.is_repo_empty():
        return {}

    args = ['git', 'log', '-1', '--pretty=%B']

    msg = check_output(args)

    # check for pull requests
    if "Merge" in msg:
        pu.info("Merge detected. Reading message from merged commit.")
        commit_id = re.search('Merge (.+?) into', msg).group(1)

        args = ['git', 'show', '-s', '--format=%B', commit_id]

        msg = check_output(args)

    if 'popper:skip[' in msg:
        pu.info("Found 'popper:skip' keyword.")
        re_expr = r'popper:skip\[(.+?)\]'
    elif 'popper:whitelist[' in msg:
        pu.info("Found 'popper:whitelist' keyword.")
        re_expr = r'popper:whitelist\[(.+?)\]'
    else:
        return project_pipelines

    try:
        pipe_list = re.search(re_expr, msg).group(1).split(',')
    except AttributeError:
        pu.fail("Error parsing commit message keyword.")

    if 'skip' in re_expr:
        pipelines = copy.deepcopy(project_pipelines)
        for p in pipe_list:
            pipelines.pop(p)
    else:
        pipelines = {}
        for p in pipe_list:
            pipelines.update({p: project_pipelines[p]})

    print('pipes: {}'.format(pipelines))
    return pipelines


def run_in_docker(project_root, pipe_n, pipe_d, env, timeout, skip,
                  ignore_errors, output_dir):

    abs_path = '{}/{}'.format(project_root, pipe_d['path'])
    docker_cmd = 'docker run --rm -v {0}:{0}'.format(project_root)
    docker_cmd += ' --workdir={}'.format(abs_path)
    docker_cmd += ' falsifiable/popper:{} run '.format(env)

    popper_flags = ' --timeout={}'.format(timeout)
    popper_flags += ' --skip {}'.format(','.join(skip)) if skip else ''
    popper_flags += ' --output {}'.format(output_dir)
    popper_flags += ' --ignore-errors' if ignore_errors else ''

    cmd = '{} {}'.format(docker_cmd, popper_flags)
    pu.info('Running in Docker with: {}'.format(cmd))
    check_output(cmd, shell=True)

    with open(os.path.join(abs_path, output_dir, 'popper_status'), 'r') as f:
        status = f.read()

    return status


def run_on_host(project_root, pipe_n, pipe_d, skip_list, timeout, output_dir):

    os.chdir(os.path.join(project_root, pipe_d['path']))

    check_output('rm -rf {}'.format(output_dir), shell=True)
    check_output('mkdir -p {}'.format(output_dir), shell=True)

    status = "SUCCESS"

    with click.progressbar(pipe_d['stages'], show_eta=False,
                           item_show_func=str,
                           bar_template='[%(bar)s] %(info)s',
                           show_percent=False) as stages:

        for stage in stages:

            stage_file = pu.get_filename('.', stage)

            if not stage_file or stage in skip_list:
                continue

            ecode = execute(stage_file, timeout, output_dir, stages)

            if ecode != 0:
                pu.info("\n\nStage '{}' failed.".format(stage))
                status = "FAIL"
                for t in ['.err', '.out']:
                    logfile = os.path.join(output_dir, stage_file + t)
                    with open(logfile, 'r') as f:
                        pu.info("\n" + t + ":\n", bold=True, fg='red')
                        pu.info(f.read())

                # Execute teardown when some stage fails and then break
                teardown_file = pu.get_filename('.', 'teardown')
                if (teardown_file and
                        stage != 'teardown' and
                        'teardown' in pipe_d['stages'] and
                        'teardown' in skip_list):
                    execute(teardown_file, timeout, output_dir)

                break

            if 'valid' in stage:
                status = "GOLD"
                fpath = os.path.join(output_dir, 'validate.sh.out')
                with open(fpath, 'r') as f:
                    validate_output = f.readlines()
                    if len(validate_output) == 0:
                        status = "SUCCESS"
                    for line in validate_output:
                        if '[true]' not in line:
                            status = "SUCCESS"

    with open(os.path.join(output_dir, 'popper_status'), 'w') as f:
        f.write(status + '\n')

    if status == "SUCCESS":
        fg = 'green'
    elif status == "GOLD":
        fg = 'yellow'
    else:
        fg = 'red'
    pu.info('\nstatus: {}\n'.format(status), fg=fg, bold=True)

    os.chdir(project_root)

    return status


def execute(stage, timeout, output_dir, bar=None):
    time_limit = time.time() + timeout
    sleep_time = 1
    out_fname = os.path.join(output_dir, stage + '.out')
    err_fname = os.path.join(output_dir, stage + '.err')

    with open(out_fname, "w") as outf, open(err_fname, "w") as errf:
        p = subprocess.Popen(os.path.join('.', stage), shell=True, stdout=outf,
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


def run_pipeline(project_root, pipe_n, pipe_d, env, timeout,
                 skip, ignore_errors, output_dir):
    timeout_parsed = pu.parse_timeout(timeout)

    skip_list = skip.split(',') if skip else []

    if os.path.isfile('/.dockerenv'):
        return run_on_host(project_root, pipe_n, pipe_d, skip_list,
                           timeout_parsed, output_dir)

    if env != 'host':
        return run_in_docker(project_root, pipe_n, pipe_d, env, timeout, skip,
                             ignore_errors, '{}/{}'.format(output_dir, env))

    return run_on_host(project_root, pipe_n, pipe_d, skip_list,
                       timeout_parsed, os.path.join(output_dir, 'host'))


class Unbuffered(object):
    def __init__(self, stream):
        self.stream = stream

    def write(self, data):
        self.stream.write(data)
        self.stream.flush()

    def __getattr__(self, attr):
        return getattr(self.stream, attr)
