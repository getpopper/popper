#!/usr/bin/env python

import click
import hcl
import os
import popper.utils as pu
import signal
import subprocess
import time
import sys

from popper.cli import pass_context
from subprocess import check_output


@click.command(
    'run', short_help='Run a workflow or action.')
@click.argument(
    'action', required=False)
@click.option(
    '--timeout',
    help='Timeout limit for pipeline. Use s for seconds, m for minutes and h '
         'for hours. A single integer can also be used to specify timeout '
         'in seconds. Use double quotes if you wish to use more than one unit.'
         'For example: --timeout "2m 20s" will mean 140 seconds. A value of 0'
         'means no timeout. Defaults to 10800 seconds',
    required=False,
    show_default=True,
    default=10800
)
@click.option(
    '--workspace',
    help='Absolute path to workspace folder.',
    required=False,
    show_default=True,
    default='/tmp/workspace'
)
@click.option(
    '--wfile',
    help='File containing the definition of the workflow.',
    required=False,
    show_default=True,
    default="./main.workflow"
)
@pass_context
def cli(ctx, action, wfile, timeout, workspace):
    """Executes one or more pipelines and reports on their status.
    """
    if not os.path.isfile(wfile):
        pu.fail("File {} does not exist".format(wfile))
    with open(wfile, 'r') as fp:
        wf = hcl.load(fp)

    normalize(wf)
    complete_graph(wf)

    pu.rmdir_content(workspace)
    os.rmdir(workspace)
    os.makedirs(workspace)
    os.environ['WORKSPACE'] = workspace

    for s in get_stages(wf):
        run_stage(wf, s, workspace, timeout)

    pu.info('Workflow finished running successfully.\n')


def normalize(wf):
    for w in wf['workflow']:
        if type(wf['workflow'][w]['resolves']) == str:
            wf['workflow'][w]['resolves'] = [wf['workflow'][w]['resolves']]
    for a in wf['action']:
        if not wf['action'][a].get('needs', None):
            continue
        if type(wf['action'][a]['needs']) == str:
            wf['action'][a]['needs'] = [wf['action'][a]['needs']]


def run_stage(wf, stage, workspace, timeout):
    for a in stage:
        run_action(wf['action'][a], workspace, timeout)


def run_action(action, workspace, timeout):

    # determine which type of action is
    #
    # convention:
    #   - if it starts with ./ is a local action
    #   - if local action has a Dockerfile, we build the container and then run
    #   - if starts with 'singularity://'
    #   - anything else we assume is a docker container

    check_secrets(action)

    if './' in action['uses']:
        # if os.path.isfile(os.path.join(action['uses'], 'Dockerfile'):
        #     build_docker(action['uses'])
        #     run_in_docker(action)
        run_on_host(action, workspace, timeout)
    else:
        run_in_docker(action, workspace, timeout)


def check_secrets(action):
    for s in action.get('secrets', []):
        if s not in os.environ:
            pu.fail('Expected secret {} not defined'.format(s))


def complete_graph(wf):
    """A GHA workflow is defined by specifying edges that point to the previous
    nodes they depend on. To make the workflow easier to process, we add
    forward edges. We also obtains the root nodes.
    """
    root_nodes = set()

    for a_name, a_values in wf['action'].items():

        a_values['name'] = a_name

        for n in a_values.get('needs', []):
            if not wf['action'][n].get('next', None):
                wf['action'][n]['next'] = set()
            wf['action'][n]['next'].add(a_name)

        if not a_values.get('needs', None):
            root_nodes.add(a_name)

    wf['root'] = root_nodes


def get_stages(wf):
    """Generator of stages. A stages is a list of actions that can be executed
    in parallel.
    """
    current_stage = wf['root']

    while current_stage:
        yield current_stage
        next_stage = set()
        for n in current_stage:
            next_stage = next_stage.union(wf['action'][n].get('next', set()))
        current_stage = next_stage


def run_in_docker(action, workspace, timeout):

    env_vars = action.get('env', {})
    for s in action.get('secrets', []):
        env_vars.update({s: os.environ[s]})

    env_flags = [' -e {}="{}"'.format(k, v) for k, v in env_vars.items()]

    docker_cmd = 'docker run --rm -v {0}:{0}'.format(workspace)
    docker_cmd += ' --workdir={} '.format(workspace)
    docker_cmd += ''.join(env_flags)
    if action.get('runs', None):
        docker_cmd += ' --entrypoint={} '.format(action['runs'])
    docker_cmd += ' {}'.format(action['uses'])
    docker_cmd += ' {}'.format(action.get('args', ''))

    pu.info('[docker] {}'.format(action['name']))

    execute(action['name'], docker_cmd, workspace, timeout)


def run_on_host(action, workspace, timeout):

    # define the input list for subprocess module
    cmd = [os.path.join('./', action.get('runs', 'entrypoint.sh'))]
    cmd.extend(action.get('args', []))

    cwd = os.getcwd()
    os.chdir(os.path.join(cwd, action['uses']))

    os.environ.update(action.get('env', {}))

    sys.stdout.write(
        '[local]  {}'.format(action['name']))

    ecode = execute(action['name'], ' '.join(cmd), workspace, timeout)

    for i in action.get('env', {}):
        os.environ.popitem(i)

    os.chdir(cwd)

    if ecode != 0:
        pu.fail("\n\nAction '{}' failed.".format(action['name']))


def execute(action_name, cmd, workspace, timeout):
    time_limit = time.time() + timeout
    sleep_time = 1

    action_name.replace(' ', '_')

    out_fname = os.path.join(os.environ['WORKSPACE'], action_name + '.out')
    err_fname = os.path.join(os.environ['WORKSPACE'], action_name + '.err')

    with open(out_fname, "w") as outf, open(err_fname, "w") as errf:
        p = subprocess.Popen(cmd, stdout=outf, stderr=errf, shell=True,
                             preexec_fn=os.setsid)

        while p.poll() is None:

            if timeout != 0.0 and time.time() > time_limit:
                os.killpg(os.getpgid(p.pid), signal.SIGTERM)
                sys.stdout.write(' time out!')
                break

            if sleep_time < 300:
                sleep_time *= 2

            for i in range(sleep_time):
                if i % 10 == 0:
                    sys.stdout.write('.')
                    sys.stdout.flush()
            time.sleep(sleep_time)

    print('')
    return p.poll()


class Unbuffered(object):
    def __init__(self, stream):
        self.stream = stream

    def write(self, data):
        self.stream.write(data)
        self.stream.flush()

    def __getattr__(self, attr):
        return getattr(self.stream, attr)
