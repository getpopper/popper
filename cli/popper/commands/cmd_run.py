#!/usr/bin/env python

import os
import sys

import click
import popper.cli
from popper.cli import pass_context
from popper.gha import Workflow
import popper.utils as pu
from ..cli import log

@click.command(
    'run', short_help='Run a workflow or action.')
@click.argument(
    'action', required=False)
@click.option(
    '--workspace',
    help='Path to workspace folder.',
    required=False,
    show_default=True,
    default=os.getcwd()
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
    '--recursive',
    help='Run any .workflow file found recursively from current path. ',
    required=False,
    is_flag=True
)
@click.option(
    '--quiet',
    help='Do not print output of actions. Instead, progress dots are printed.',
    required=False,
    is_flag=True
)
@click.option(
    '--debug',
    help=(
        'Verbose output of ALL subcommands executed by popper '
        '(overrides --debug)'),
    required=False,
    is_flag=True
)
@click.option(
    '--dry-run',
    help='A dry run for a workflow',
    required=False,
    is_flag=True
)
@click.option(
    '--parallel',
    help='Executes actions in stages in parallel',
    required=False,
    is_flag=True
)
@click.option(
    '--log-file',
    help='Generates a log file at the mentioned location',
    required=False
)
@pass_context
def cli(ctx, action, wfile, workspace, reuse,
        recursive, quiet, debug, dry_run, parallel, log_file):
    """Executes one or more pipelines and reports on their status.
    """
    popper.scm.get_git_root_folder()
    level = 'ACTION_INFO'
    if quiet:
        level = 'INFO'
    if debug:
        level = 'DEBUG'
    log.setLevel(level)
    if recursive:
        wfile_list = pu.find_recursive_wfile()
        if not wfile_list:
            log.fail("Recursive search couldn't find any .workflow files ")
        for wfile in wfile_list:
            log.info("Found and running workflow at " + wfile)
            run_pipeline(action, wfile, workspace, reuse,
                         dry_run, parallel, log_file)
    else:
        run_pipeline(action, wfile, workspace, reuse,
                     dry_run, parallel, log_file)


def run_pipeline(action, wfile, workspace, reuse,
                 dry_run, parallel, log_file):
    pipeline = Workflow(wfile, workspace, dry_run,
                        reuse, parallel)

    # Saving workflow instance for signal handling
    popper.cli.interrupt_params = pipeline

    if reuse:
        log.warn("using --reuse ignores any changes made to an action")
        log.warn("or to an action block in the workflow.")

    if parallel:
        if sys.version_info[0] < 3:
            log.fail('--parallel is only supported on Python3')
        log.warn("using --parallel may result in interleaved output.")
        log.warn("You may use --quiet flag to avoid confusion.")

    pipeline.run(action, reuse, parallel)

    if action:
        log.info('Action "{}" finished successfully.'.format(action))
    else:
        log.info('Workflow finished successfully.')
