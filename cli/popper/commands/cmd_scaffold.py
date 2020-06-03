import os

import click

from popper.cli import pass_context, log


@click.command("scaffold", short_help="Generate a minimal workflow.")
@click.option(
    "-f",
    "--file",
    help="Name of file where to write the generated workflow.",
    required=False,
    default="wf.yml",
)
@pass_context
def cli(ctx, file):
    """Generates a minimal workflow that can be used as starting point."""
    main_workflow_content = """steps:

- uses: "popperized/bin/sh@master"
  args: ["ls"]

- uses: "docker://alpine:3.11"
  args: ["ls"]
"""

    if os.path.exists(file):
        log.fail(f"File {file} already exists")

    with open(file, "w") as f:
        f.write(main_workflow_content)

    log.info("Successfully generated a workflow scaffold.")
