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
from collections import defaultdict


@click.command('run',
               short_help='Run one or more pipelines and report on their '
                          'status.')
@click.argument('pipeline', required=False)
@click.option(
    '--timeout',
    help='Timeout limit for pipeline. Use s for seconds, m for minutes and h '
         'for hours. A single integer can also be used to specify timeout '
         'in seconds. Use double quotes if you wish to use more than one unit.'
         'For example: --timeout "2m 20s" will mean 140 seconds. A value of 0'
         'means no timeout. Defaults to 10800 seconds',
    required=False,
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
    '--requirement-level',
    type=click.Choice(['warn', 'ignore', 'fail']), default='fail',
    help='Determines how to handle missing requirements. warn simply'
         'emits a wanring and continues normally; ignore runs the'
         'specified pipelines despite missing unfulfilled'
         'requirements; fail exits with an error on unfilfilled'
         'requirements.'
)
@click.option(
    '--no-badge-update',
    help='Do not update the status of the pipeline against the badge server.',
    is_flag=True,
    required=False,
)
@pass_context
def cli(ctx, pipeline, timeout, skip, ignore_errors, output,
        no_badge_update, requirement_level):
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

    pipelines = {pipe_n: pipe_c for pipe_n, pipe_c in pipelines.items()
                 if check_requirements(pipe_n, pipe_c, requirement_level)}

    pipelines = check_skiplist(pipelines, skip)

    if not len(pipelines):
        pu.info("No pipelines to execute")
        sys.exit(0)

    status = run_pipelines(pipelines, project_root, timeout, skip,
                           ignore_errors, output)

    os.chdir(cwd)

    if os.environ.get('CI', False) and not no_badge_update:
        update_badge(status)

    if status == 'FAIL':
        pu.fail("Failed to execute pipeline")


def run_pipelines(pipelines, project_root, timeout, skip,
                  ignore_errors, output):
    status = 'SUCCESS'
    for pipe_n, pipe_d in pipelines.items():
        envs = list(pipe_d.get('envs', ['host']))
        if 'host' in envs:
            # Makes sure execution starts with host
            envs.insert(0, envs.pop(envs.index('host')))
        for env in envs:
            executions = get_executions_for_pipeline(pipe_d.get('parameters'))
            status = run_pipeline(project_root, pipe_n, pipe_d, env,
                                  timeout, skip, ignore_errors, output,
                                  executions=executions,
                                  args=pipe_d['envs'][env]['args'])
            if status == 'FAIL' and not ignore_errors:
                return status
    return status


def get_executions_for_pipeline(env_vars):
    executions = []
    if env_vars:
        for env_var in env_vars:
            executions.append(env_var)
    else:
        executions.append("")
    return executions


def set_env_vars(env_vars):
    for env_var in env_vars:
        os.environ[env_var] = env_vars[env_var]


def unset_env_vars(env_vars):
    for env_var in env_vars:
        del os.environ[env_var]


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


def check_skiplist(pipelines, skiplist):
    """
    Filters a list of pipelines based on a list of pipelines and stages to
    skip.
    """
    if skiplist is None:
        return pipelines

    new_pipelist = {}

    pu.info(skiplist)

    skiplist = set(skiplist.split(','))

    # parse stages to skip in the form of pipe:stage
    stage_skip = defaultdict(set)
    for item in skiplist:
        tup = item.split(':')
        if len(tup) > 1:
            pipe, stage_n = tup
            stage_skip[pipe].add(stage_n)

    # only include pipes and stages that aren't in the skip list
    for name, pipeline in pipelines.items():
        if name in skiplist:
            continue
        stages = [stage for stage in pipeline['stages']
                  if stage not in skiplist and stage not in stage_skip[name]]

        pipeline = dict(pipeline)
        pipeline['stages'] = stages

        new_pipelist[name] = pipeline

    return new_pipelist


def update_badge(status):
    if pu.is_repo_empty():
        pu.warn('No commit log found. Skipping badge server update.')
        return

    remote_url = pu.get_remote_url()
    if not remote_url:
        pu.warn('No remote url found. Skipping badge server update.')
        return

    baseurl = pu.read_config().get(
        'badge-server-url', 'http://badges.falsifiable.us'
    )
    org, repo = remote_url.split('/')[-2:]
    badge_server_url = '{}/{}/{}'.format(baseurl, org, repo)
    branch_name = check_output(
        ['git', 'rev-parse', '--abbrev-ref', 'HEAD']
    )[:-1]
    data = {
        'timestamp': int(time.time()),
        'commit_id': pu.get_head_commit(),
        'status': status,
        'branch': branch_name,
    }
    try:
        r = requests.post(badge_server_url, data=data)
        if r.status_code != 201 and r.status_code != 200:
            pu.warn("Could not create a record on the badge server.")
        else:
            pu.info(r.json()['message'], fg="green")
    except requests.exceptions.RequestException:
        pu.warn("Could not communicate with the badge server.")


def pipelines_from_commit_message(project_pipelines):

    # check if repo is empty
    if pu.is_repo_empty():
        return {}

    args = ['git', 'log', '-1', '--pretty=%B']

    msg = str(check_output(args))

    # check for pull requests
    if 'Merge' in msg:
        pu.info("Merge detected. Reading message from merged commit.")
        commit_id = re.search(r'Merge (.+?) into', msg).group(1)

        args = ['git', 'show', '-s', '--format=%B', commit_id]

        msg = str(check_output(args))

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

    print('Only running pipes: {}'.format(', '.join(pipelines.keys())))
    return pipelines


def check_requirements(pipe_n, pipeline, requirement_level):
    if 'requirements' not in pipeline:
        return True

    var_reqs = pipeline['requirements'].get('vars', [])
    bin_reqs = pipeline['requirements'].get('bin', [])

    missing_vars = [envvar for envvar in var_reqs if envvar not in os.environ]
    missing_binaries = [bin for bin in bin_reqs if not bin_exists(bin)]

    missing_versions = [bin_requirements(bin) for bin in bin_reqs
                        if bin not in missing_binaries]
    missing_versions = [msg for msg in missing_versions if msg is not None]

    msg = ""
    if missing_vars:
        msg += ('Required environment variables for pipeline {} unset: {}\n'
                .format(pipe_n, ','.join(missing_vars)))
    if missing_binaries:
        msg += ('Required binaries for pipeline {} not available: {}\n'
                .format(pipe_n, ','.join(missing_binaries)))
    if missing_versions:
        msg += ('Requirements for pipeline {} not fulfilled:\n{}\n'
                .format(pipe_n, '\n'.join(missing_versions)))
    if msg:

        if requirement_level == 'fail':
            pu.fail(msg)

        pu.warn(msg)

        if requirement_level == 'warn':
            pu.info('Skipping pipeline {}'.format(pipe_n))

        return requirement_level == 'ignore'

    return True


def bin_requirements(bin):

    if ':' not in bin:
        return None

    binary = re.search('(.+):', bin).group(1)

    version = str(check_output(binary + " --version", shell=True))

    required_version = re.search(r'\+?(\d+(?:\.\d+)*)', bin).group(1)
    version = re.search(r'(\d+(\.\d+)*\.?)', version).group(1)

    meets_reqs = required_version <= version \
        if '+' in bin else version.startswith(required_version)

    op = '+' if '+' in bin else ""

    msg = 'Required ' + binary + ' version: ' + op + \
          required_version + ' - Version found: ' + version

    return msg if not meets_reqs else None


def bin_exists(bin):
    binary = re.search('(.+):', bin).group(1) if ':' in bin else bin

    try:
        check_output(binary + " --version", shell=True,
                     stderr=subprocess.STDOUT)
        return True
    except subprocess.CalledProcessError:
        return False


def run_in_docker(project_root, pipe_n, pipe_d, env, timeout, skip,
                  ignore_errors, output_dir, env_vars, args):

    abs_path = '{}/{}'.format(project_root, pipe_d['path'])
    docker_cmd = 'docker run --rm -v {0}:{0}'.format(project_root)
    docker_cmd += ' --workdir={} '.format(abs_path)
    docker_cmd += ' '.join(args)
    docker_cmd += ''.join([' -e {0}="{1}"'.format(k, env_vars[k])
                           for k in env_vars]) if env_vars else ''

    if '/' in env:
        img = env
    else:
        img = 'falsifiable/popper:{}'.format(env)

    docker_cmd += ' {} run '.format(img)

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
                           item_show_func=(lambda s: status if s is None
                                           else str(s)),
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
            sys.stdout.write('Running: {}'.format(stage))

        while p.poll() is None:

            if timeout != 0.0 and time.time() > time_limit:
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
                 skip, ignore_errors, output_dir, executions, args):
    if timeout is None:
        timeout = pipe_d.get('timeout', "10800s")
    timeout_parsed = pu.parse_timeout(timeout)

    skip_list = skip.split(',') if skip else []

    click.echo('Executing pipeline: {}'.format(pipe_n))

    status = 'SUCCESS'
    for number_of_run, env_vars in enumerate(executions):
        set_env_vars(env_vars)
        if os.path.isfile('/.dockerenv'):
            status = run_on_host(project_root, pipe_n, pipe_d, skip_list,
                                 timeout_parsed, output_dir)
        elif env != 'host':
            status = \
                run_in_docker(project_root, pipe_n, pipe_d, env,
                              timeout, skip, ignore_errors, '{}/{}/{}'.
                              format(output_dir, env.replace('/', '_'),
                                     number_of_run if env_vars else ""),
                              env_vars, args)
        else:
            status = \
                run_on_host(project_root, pipe_n, pipe_d, skip_list,
                            timeout_parsed, os.path. join(output_dir, 'host',
                                                          str(number_of_run)
                                                          if env_vars else ""))
        unset_env_vars(env_vars)
        if status == 'FAIL' and not ignore_errors:
            break

    return status


class Unbuffered(object):
    def __init__(self, stream):
        self.stream = stream

    def write(self, data):
        self.stream.write(data)
        self.stream.flush()

    def __getattr__(self, attr):
        return getattr(self.stream, attr)
