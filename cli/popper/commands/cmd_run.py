import os
import re
import sys

import click

import popper.cli
from popper.cli import pass_context, log
from popper.gha import WorkflowRunner
from popper.parser import Workflow
from popper import utils as pu, scm
from popper import log as logging


@click.command(
    'run', short_help='Run a workflow or action.')
@click.argument(
    'action', required=False)
@click.option(
    '--on-failure',
    help='The action to run if there is a failure.',
    required=False,
    default=None
)
@click.option(
    '--with-dependencies',
    help='Run the action with all its dependencies.',
    required=False,
    is_flag=True
)
@click.option(
    '--workspace',
    help='Path to workspace folder.',
    required=False,
    show_default=True,
    default=popper.scm.get_git_root_folder()
)
@click.option(
    '--reuse',
    help='Reuse containers between executions (persist container state).',
    required=False,
    is_flag=True,
)
@click.option(
    '--wfile',
    help=(
        'File containing the definition of the workflow. '
        '[default: ./github/main.workflow OR ./main.workflow]'
    ),
    required=False,
    default=None
)
@click.option(
    '--skip',
    help=('Skip the list of actions specified.'),
    required=False,
    default=list(),
    multiple=True
)
@click.option(
    '--recursive',
    help='Run any .workflow file found recursively from current path.',
    required=False,
    is_flag=True
)
@click.option(
    '--quiet',
    help='Do not print output generated by actions.',
    required=False,
    is_flag=True
)
@click.option(
    '--debug',
    help=(
        'Generate detailed messages of what popper does (overrides --quiet)'),
    required=False,
    is_flag=True
)
@click.option(
    '--dry-run',
    help='A dry run for a workflow.',
    required=False,
    is_flag=True
)
@click.option(
    '--parallel',
    help='Executes actions in stages in parallel.',
    required=False,
    is_flag=True
)
@click.option(
    '--log-file',
    help='Path to a log file. No log is created if this is not given.',
    required=False
)
@click.option(
    '--skip-clone',
    help='Skip pulling docker or singularity images.',
    required=False,
    is_flag=True
)
@click.option(
    '--skip-pull',
    help='Skip cloning actions from github.',
    required=False,
    is_flag=True
)
@pass_context
def cli(ctx, action, wfile, skip_clone, skip_pull, skip, workspace, reuse,
        recursive, quiet, debug, dry_run, parallel,
        log_file, with_dependencies, on_failure):
    """Executes one or more pipelines and reports on their status.
    """
    popper.scm.get_git_root_folder()
    level = 'ACTION_INFO'
    if quiet:
        level = 'INFO'
    if debug:
        level = 'DEBUG'
    log.setLevel(level)
    if log_file:
        logging.add_log(log, log_file)

    if os.environ.get('CI') == "true":
        # If running in CI environment, manipulate the workflow files.
        wfile_list = pu.find_recursive_wfile()
        log.info("Running in CI environment..")
        wfile_list = workflows_from_commit_message(wfile_list)
    else:
        # If running in a non-CI environment.
        if recursive:
            wfile_list = pu.find_recursive_wfile()
        else:
            wfile_list = [wfile]

    # If now workflow files are left to process.
    if not wfile_list:
        log.fail("No workflow to execute.")

    for wfile in wfile_list:
        wfile = pu.find_default_wfile(wfile)
        log.info("Found and running workflow at " + wfile)
        run_pipeline(action, wfile, skip_clone, skip_pull, skip, workspace,
                     reuse, dry_run, parallel, with_dependencies, on_failure)


def run_pipeline(action, wfile, skip_clone, skip_pull, skip, workspace, reuse,
                 dry_run, parallel, with_dependencies, on_failure):

    # Initialize a Worklow. During initialization all the validation
    # takes place automatically.
    wf = Workflow(wfile)
    pipeline = WorkflowRunner(wf)

    # Saving workflow instance for signal handling
    popper.cli.interrupt_params['parallel'] = parallel

    if reuse:
        log.warn("Using --reuse ignores any changes made to an action's logic "
                 "or to an action block in the .workflow file.")

    if parallel:
        if sys.version_info[0] < 3:
            log.fail('--parallel is only supported on Python3')
        log.warn("Using --parallel may result in interleaved output. "
                 "You may use --quiet flag to avoid confusion.")

    if skip_clone:
        log.warn("Please make sure that all the required action repositories "
                 "are available locally.")

    if skip_pull:
        log.warn("Please make sure that all the required images are "
                 "present locally.")

    try:
        pipeline.run(action, skip_clone, skip_pull, skip, workspace, reuse,
                     dry_run, parallel, with_dependencies)
    except SystemExit as e:
        if (e.code is not 0) and on_failure:
            pipeline.run(on_failure, skip_clone, skip_pull, list(), workspace,
                         reuse, dry_run, parallel, with_dependencies)
        else:
            raise

    if action:
        log.info('Action "{}" finished successfully.'.format(action))
    else:
        log.info('Workflow finished successfully.')


def workflows_from_commit_message(workflows):
    head_commit = scm.get_head_commit()

    if not head_commit:
        return workflows

    msg = head_commit.message

    if 'Merge' in msg:
        log.info("Merge detected. Reading message from merged commit.")
        if len(head_commit.parents) == 2:
            msg = head_commit.parents[0].message

    if 'popper:skip[' in msg:
        log.info("Found 'popper:skip' keyword.")
        re_expr = r'popper:skip\[(.+?)\]'
    elif 'popper:whitelist[' in msg:
        log.info("Found 'popper:whitelist' keyword.")
        re_expr = r'popper:whitelist\[(.+?)\]'
    else:
        return workflows

    try:
        workflow_list = re.search(re_expr, msg).group(1).split(',')
    except AttributeError:
        log.fail("Error parsing commit message keyword.")

    if 'skip' in re_expr:
        for wf in workflow_list:
            if wf in workflows:
                workflows.remove(wf)
            else:
                log.warn('Workflow {} was not found.'.format(wf))
    else:
        workflows = workflow_list

    print('Only running workflows: {}'.format(', '.join(workflows)))
    return workflows
