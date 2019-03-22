#!/usr/bin/env python

import click
import os
import popper.utils as pu

from popper.gha import Workflow
from popper.cli import pass_context


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
@pass_context
def cli(ctx, action, wfile, workspace, reuse,
        recursive, quiet, debug, dry_run):
    """Executes one or more pipelines and reports on their status.
    """
    if recursive:
        for root, dirs, files in os.walk('.'):
            for file in files:
                if file.endswith('.workflow'):
                    wfile = os.path.join(root, file)
                    wfile = os.path.abspath(wfile)
                    pu.info("Found and running workflow at "+wfile+"\n")
                    run_pipeline(
                        action, wfile, workspace, reuse, quiet, debug, dry_run)
    else:
        run_pipeline(action, wfile, workspace, reuse, quiet, debug, dry_run)


def run_pipeline(action, wfile, workspace, reuse, quiet, debug, dry_run):
    pipeline = Workflow(wfile, workspace, quiet, debug, dry_run)

    if reuse:
        pu.info(
            "\n  " +
            "WARNING: using --reuse ignores any changes made to an action" +
            "\n  " +
            "or to an action block in the workflow.\n\n"
        )

    pipeline.run(action, reuse)

    if action:
        pu.info('\nAction "{}" finished successfully.\n\n'.format(action))
    else:
        pu.info('\nWorkflow finished successfully.\n\n')
