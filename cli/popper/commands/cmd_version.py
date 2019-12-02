import click
import logging

from popper import __version__ as popper_version
from popper.cli import pass_context, log

log = logging.getLogger('popper')
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
print(ch)
log.addHandler(ch)
print(log.handlers)
log.RemoveHandler(log.handlers[0])
print(log.handlers)
# log.RemoveHandler(log.handlers[0])
# print(log.handlers)
print(log)


@click.command('version', short_help='Show version of Popper and exit.')
@pass_context
def cli(ctx):
    """Displays version of Popper and exit."""
    log.info('Popper version {}'.format(popper_version))
