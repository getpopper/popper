import click
import popper.utils as pu
from .. import __version__ as popper_version
from ..cli import pass_context


@click.command('version', short_help='Show version of Popper and exit.')
@pass_context
def cli(ctx):
    """Displays version of Popper and exit."""
    pu.info('popper version ' + popper_version, fg='blue', bold=True)
