#!/usr/bin/env python

import click
import popper.utils as pu

from popper.gha import Workflow
from popper.cli import pass_context


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
    default=".github/main.workflow"
)
@pass_context
def cli(ctx, action, wfile, timeout, workspace):
    """Executes one or more pipelines and reports on their status.
    """
    pipeline = Workflow(wfile)
    pipeline.workspace = workspace
    pipeline.timeout = timeout

    pipeline.run(action)

    if action:
        pu.info('\nAction "{}" finished successfully.\n\n'.format(action))
    else:
        pu.info('\nWorkflow finished successfully.\n\n')
