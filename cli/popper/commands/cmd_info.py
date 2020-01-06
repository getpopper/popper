import click

from popper import utils as pu
from popper.cli import log, pass_context


@click.argument('action', required=True)
@click.option(
    '--update-cache',
    help='Update the action metadata cache before looking for info.',
    is_flag=True
)
@click.command('info', short_help='Show details about an action.')
@pass_context
def cli(ctx, action, update_cache):

    metadata = pu.fetch_metadata(update_cache)
    action_metadata = metadata.get(action, None)

    if not action_metadata:
        log.fail('Unable to find metadata for given action.')

    if not action_metadata['repo_readme']:
        log.fail('This repository does not have a README.md file.')

    log.info(action_metadata['repo_readme'])
