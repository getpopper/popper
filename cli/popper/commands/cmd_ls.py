import os
import click
import shutil
import popper.utils as pu
from popper.cli import pass_context


@click.command(
    'ls',
    short_help='Show list of pipelines in current project.')
@pass_context
def cli(ctx):
    """Used to list down the avaliable pipelines
    in a popper repository

    Example:

    > popper ls
     - experiment-1
     - experiment-2

    """

    pipelines = list(pu.read_config()['pipelines'].keys())
    if 'paper' in pipelines:
        pipelines.remove('paper')

    if len(pipelines) == 0:
        pu.info("There are no pipelines in this repository", fg="red")
    else:
        pu.info("The available pipelines are :\n", fg="cyan")
        pu.print_yaml(pipelines, fg="cyan")
