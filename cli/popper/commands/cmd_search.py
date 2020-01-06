import click

from popper import utils as pu
from popper.cli import log, pass_context


@click.argument(
    'keyword',
    required=True
)
@click.option(
    '--update-cache',
    help=('Update the action metadata cache before searching.'),
    is_flag=True
)
@click.option(
    '--include-readme',
    help=('Include README while searching for matching actions.'),
    is_flag=True
)
@click.command('search', short_help='Search for actions on Github.')
@pass_context
def cli(ctx, keyword, update_cache, include_readme):
    metadata = pu.fetch_metadata(update_cache)
    result = search(metadata, keyword, include_readme)
    log.info('Search Results : \n')
    if result:
        for action in result:
            log.info('> {}\n'.format(action))
    else:
        log.info('No matching actions found.\n')


def search(metadata, keyword, include_readme):
    """Search for the keyword in the repo metadata.

    Args:
        metadata (dict) : The dict on which to run search.
        keyword (str) : The keyword to search for.
        include_readme (bool) : Flag variable indicating whether
        to search keyword inside the README.md or not.

    Returns:
        list : List of repo names which confirm with
        the search.
    """
    keyword = keyword.lower()
    result = list()
    for action, action_metadata in metadata.items():
        if keyword in action.lower():
            result.append(action)
        elif include_readme:
            if keyword in action_metadata['repo_readme'].lower():
                result.append(action)
    return result
