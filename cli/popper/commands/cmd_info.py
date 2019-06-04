import sys

import click

from popper import utils as pu
from popper.cli import log, pass_context


@click.argument('action', required=True)
@click.option(
    '--full',
    help='Show full content of the README.',
    is_flag=True
)
@click.option(
    '--update-cache',
    help='Update the action metadata cache before looking for info.',
    is_flag=True
)
@click.command('info', short_help='Show details about an action.')
@pass_context
def cli(ctx, action, full, update_cache):

    try:
        org, repo = action.split('/')
    except ValueError:
        log.fail('Bad action name. Required format {org}/{repo}')

    metadata = pu.fetch_metadata(update_cache)

    repo_metadata = None
    if metadata.get(org, None):
        if metadata[org].get(repo, None):
            repo_metadata = metadata[org][repo]

    if not repo_metadata:
        log.fail('Unable to find metadata for given pipeline.')

    if not repo_metadata.get('repo_readme', None):
        log.fail('This repository does not have a README.md file.')

    if full:
        log.info(repo_metadata['repo_readme'])
    else:
        lines = repo_metadata['repo_readme'].split('\n')
        if len(lines) <= 2:
            log.info(repo_metadata['repo_readme'])
        else:
            for l in lines[2:]:
                if not l:
                    break
                log.info(l)
