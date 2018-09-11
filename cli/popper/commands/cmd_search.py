import click
import sys
import popper.utils as pu

from popper.cli import pass_context
from popper.exceptions import BadArgumentUsage

# For compatibility between python 2.x and 3.x versions
try:
    FileNotFoundError
except NameError:
    FileNotFoundError = IOError


@click.command(
    'search',
    short_help='Search for pipelines on Github matching one or more keywords.')
@click.argument('keywords', required=False)
@click.option(
    '--skip-update',
    help=('Skip updating the metadata and search on the local cache'),
    is_flag=True
)
@click.option(
    '--add',
    help=('Add a pipeline source (format: <org>/<repo> or <org>)'),
)
@click.option(
    '--rm',
    help=('Remove a pipeline source (format: <org>/<repo> or <org>)'),
)
@click.option(
    '--ls',
    help=('List all the repositories available to search'),
    is_flag=True
)
@click.option(
    '--include-readme',
    help=('Include readme when searching for matching pipelines.'),
    is_flag=True
)
@pass_context
def cli(ctx, keywords, skip_update, add, rm, ls, include_readme):
    """Searches for pipelines on Github matching the given keyword(s).

    The list of repositories or organizations scraped for pipelines is
    specified in the 'popperized' list in the .popper.yml file. By default,
    https://github.com/popperized is added to the list.

    If no keywords are specified, a list of all the pipelines from all
    organizations (in the .popper.yml file) and repositories will be shown.

    This commands makes use of Github's API, which has a limit on the number of
    requests per hour that an unauthenticated user can make. If you reach this
    limit, you can provide a Github API token via a POPPER_GITHUB_API_TOKEN
    environment variable. If defined, this variable is used to obtain the token
    when executing HTTP requests.

    Example:

        popper search quiho

    Would result in:

        popperized/quiho-popper/single-node

    The format of search output is <org>/<repo>/<pipeline-name>. To add
    organizations or repositories to the list of pipeline sources:

        popper search --add org/repo
        popper search --add entireorg

    To remove one:

        popper search --rm org/repo
        popper search --rm entireorg

    To view the list repositories that are available to the search command:

        popper search --ls
    """
    if ((rm and add) or (rm and ls) or (add and ls)):
        raise BadArgumentUsage("Only one of 'add', 'rm' and 'ls' accepted.")

    if (rm or add or ls) and keywords:
        raise BadArgumentUsage("Search cannot be combined with other flags.")

    config = pu.read_config()
    sources = pu.get_search_sources(config)

    if add:
        if len(add.split('/')) > 2:
            pu.fail("Bad source naming format. See 'popper search --help'.")
        if add in sources:
            pu.info('{} is already a search source.'.format(add))
            sys.exist(0)

        sources.append(add)

        config['search_sources'] = sources
        pu.write_config(config)
        sys.exit(0)

    if rm:
        if rm not in sources:
            pu.info("'{}' is not a search source.".format(rm))
            sys.exit(0)

        sources.remove(rm)

        config['search_sources'] = sources
        pu.write_config(config)
        sys.exit(0)

    if len(sources) == 0:
        pu.fail('No source for popper pipelines defined! Add one first.')

    pipeline_meta = pu.fetch_pipeline_metadata(skip_update)
    result = search_pipelines(pipeline_meta, keywords, include_readme)

    pu.info('Matching pipelines:')
    pu.print_yaml(result)


def search_pipelines(meta, keywords, include_readme):
    result = []
    for pipe in pipeline_name_list(meta):
        if not keywords:
            result.append(pipe)
        else:
            for key in keywords.split(' '):
                if key in pipe:
                    result.append(pipe)
                    break
                if include_readme:
                    p = pipe.split('/')
                    readme = meta[p[0]][p[1]]['pipelines'][p[2]]['readme']
                    if key.lower() in readme.lower():
                        result.append(pipe)
    return result


def pipeline_name_list(meta):
    for org in meta:
        for repo in meta[org]:
            if 'pipelines' not in meta[org][repo]:
                continue
            for pipe in meta[org][repo]['pipelines']:
                if pipe == 'paper':
                    continue
                yield '{}/{}/{}'.format(org, repo, pipe)
