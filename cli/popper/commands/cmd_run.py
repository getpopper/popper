#!/usr/bin/env python

import os
import sys

import click
import popper.cli
from popper import utils as pu
from popper.cli import pass_context
from popper.gha import Workflow


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
@pass_context
def cli(ctx, action, wfile, workspace, reuse,
        recursive, quiet, debug, dry_run, parallel):
    """Executes one or more pipelines and reports on their status.
    """
    popper.scm.get_git_root_folder()
    if recursive:
        wfile_list = pu.find_recursive_wfile()
        for wfile in wfile_list:
            pu.info("Found and running workflow at "+wfile+"\n")
            run_pipeline(action, wfile, workspace, reuse, quiet,
                         debug, dry_run, parallel)
    else:
        run_pipeline(action, wfile, workspace, reuse, quiet,
                     debug, dry_run, parallel)


def run_pipeline(action, wfile, workspace, reuse,
                 quiet, debug, dry_run, parallel):
    pipeline = Workflow(wfile, workspace, quiet, debug, dry_run,
                        reuse, parallel)

    # Saving workflow instance for signal handling
    popper.cli.interrupt_params = pipeline

    if reuse:
        pu.warn(
            "\n  " +
            "using --reuse ignores any changes made to an action" +
            "\n  " +
            "or to an action block in the workflow.\n\n"
        )

    if parallel:
        if sys.version_info[0] < 3:
            pu.fail('--parallel is only supported on Python3')

        pu.warn(
            "\n  " +
            "using --parallel may result in interleaved ouput." +
            "\n  " +
            "You may use --quiet flag to avoid confusion.\n\n"
        )

    pipeline.run(action, reuse, parallel)

    if action:
        pu.info(
            prefix='\nAction "{}" finished successfully.\n\n'.format(action),
            msg='')
    else:
        pu.info('\nWorkflow finished successfully.\n\n')
