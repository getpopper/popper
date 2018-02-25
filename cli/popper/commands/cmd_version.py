import click
import popper.utils as pu
import popper
from popper.cli import pass_context


@click.command('version', short_help='Show version of Popper and exit.')
@pass_context
def cli(ctx):
    """Displays version of Popper and exit."""
    pu.info(popper.__version__)
