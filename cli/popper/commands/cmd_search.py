import os
import sys

import click

from popper import utils as pu
from popper.cli import log, pass_context


@click.argument(
    'keywords',
    required=True
)
@click.option(
    '--update-cache',
    help=('Skip updating the metadata and search on the local cache.'),
    is_flag=True
)
@click.option(
    '--include-readme',
    help=('Include README while searching for matching actions.'),
    is_flag=True
)
@click.command('search', short_help='Search for actions on Github.')
@pass_context
def cli(ctx, keywords, update_cache, include_readme):
    metadata = pu.fetch_metadata(update_cache)
    result = search(metadata, keywords, include_readme)
    result = list(map(lambda x: x[0] + '/' + x[1], result))
    log.info('Matched actions : {}'.format(result))


def search(metadata, keyword, include_readme):
    """Search for the keyword in the repo metadata.

    Args:
        metadata (dict) : The dict on which to run search.
        keyword (str) : The keyword to search for.
        include_readme (bool) : Flag variable indicating whether
        to search keyword inside the README.md or not.

    Returns:
        list : List of repo metadata dicts which confirm with
        the search.
    """
    result = list()
    for org, repos_in_org in metadata.items():
        for repo, repo_metadata in repos_in_org.items():
            if keyword in repo:
                result.append((org, repo))
            elif include_readme and repo_metadata.get('repo_readme', None):
                if keyword in repo_metadata['repo_readme']:
                    result.append((org, repo))
    return result
