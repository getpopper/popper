import click
from .. import __version__ as popper_version
from ..cli import pass_context
from ..cli import log


@click.command('version', short_help='Show version of Popper and exit.')
@pass_context
def cli(ctx):
    """Displays version of Popper and exit."""
    log.info('popper version {}'.format(popper_version))
