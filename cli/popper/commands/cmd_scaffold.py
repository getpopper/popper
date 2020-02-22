import os

import click

from popper.cli import pass_context, log


@click.command('scaffold', short_help='Generate a minimal workflow.')
@click.option(
    '-f',
    '--wfile',
    help='Name of file where to write the generated workflow.',
    required=False,
    default='wf.yml'
)
@pass_context
def cli(ctx, wfile):
    """Generates a minimal workflow that can be used as starting point."""
    main_workflow_content = """steps:

- uses: "popperized/bin/sh@master"
  args: "ls"

- uses: "docker://alpine:3.11"
  args: ["ls"]
"""

    if os.path.exists(wfile):
        log.fail(f'File {wfile} already exists')

    with open(wfile, 'w') as f:
        f.write(main_workflow_content)

    log.info('Successfully generated a workflow scaffold.')
