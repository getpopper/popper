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
    """Finds out the metadata for the given action. This command searches for
    the Readme file in the repository of the action.

    Args:
      ctx(Popper.cli.context): For process inter-command communication
            context is used.For reference visit
            https://click.palletsprojects.com/en/7.x/commands/#nested-handling-and-contexts .
      action(str): The action that is passed as an argument.
      update_cache(bool): The flag for checking the argument for updating
                          cache.

    Returns:
        None
    """
    metadata = pu.fetch_metadata(update_cache)
    action_metadata = metadata.get(action, None)

    if not action_metadata:
        log.fail('Unable to find metadata for given action.')

    if not action_metadata['repo_readme']:
        log.fail('This repository does not have a README.md file.')

    log.info(action_metadata['repo_readme'])
