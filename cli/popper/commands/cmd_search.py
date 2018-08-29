import click
import os
import sys
import popper.utils as pu
import yaml

from collections import defaultdict
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
@pass_context
def cli(ctx, keywords, skip_update, add, rm, ls):
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
    sources = config['popperized']

    if add:
        if len(add.split('/')) > 2:
            pu.fail("Bad source naming format. See 'popper search --help'.")
        if add in sources:
            pu.info('{} is already a search source.'.format(add))
            sys.exist(0)

        sources.append(add)

        config['popperized'] = sources
        pu.write_config(config)
        sys.exit(0)

    if rm:
        if rm not in sources:
            pu.info("'{}' is not a search source.".format(rm))
            sys.exit(0)

        sources.remove(rm)

        config['popperized'] = sources
        pu.write_config(config)
        sys.exit(0)

    if len(sources) == 0:
        pu.fail('No source for popper pipelines defined! Add one first.')

    if skip_update:
        pipeline_meta = load_pipeline_metadata()
    else:
        pipeline_meta = update_pipeline_metadata(sources)

    if ls:
        for pipe in pipeline_list(pipeline_meta):
            pu.info('- {}'.format(pipe))
        sys.exit(0)

    search_pipelines(pipeline_meta, keywords)


def update_pipeline_metadata(sources):
    meta = defaultdict(dict)
    repos = []

    for s in sources:
        if '/' in s:
            repos.append(s)
        else:
            for repo in pu.repos_in_org(s):
                repos.append(s+'/'+repo)

    with click.progressbar(
            repos,
            show_eta=False,
            bar_template='[%(bar)s] %(info)s | %(label)s',
            show_percent=True) as bar:
        for r in bar:
            bar.label = "Fetching pipeline metadata from '{}'".format(r)
            update_metadata_for_repo(r, meta)

    project_root = pu.get_project_root()

    with open(os.path.join(project_root, '.pipeline_cache'), 'w') as f:
        yaml.dump(dict(meta), f)

    return meta


def update_metadata_for_repo(orgrepo, meta):
    org, repo = orgrepo.split('/')
    config = pu.read_config_remote(org, repo)
    if not config:
        return
    meta[org][repo] = config


def load_pipeline_metadata():
    project_root = pu.get_project_root()

    with open(os.path.join(project_root, '.pipeline_cache'), 'r') as f:
        meta = yaml.load(f)

    return meta


def search_pipelines(meta, keywords):
    result = []
    for pipe in pipeline_list(meta):
        if not keywords:
            result.append(pipe)
        elif l_distance(pipe.lower(), keywords.lower()) < 1:
            result.append(pipe)

    return result


def pipeline_list(meta):
    for org in meta:
        for repo in meta[org]:
            pu.info("repo: {}".format(repo))
            pu.info("pipelines: {}".format(meta[org][repo]['pipelines']))
            for pipe in meta[org][repo]:
                yield '{}/{}/{}'.format(org, repo, pipe)


def l_distance(a, b):
    """A modified version of the Levenshtein Distance algorithm to find
    word level edit distances between two sentences.

    Args:
        a, b (str): The words between which the Levenshtein distance
                        is to be calculated.
    Returns:
        ldist (int): Levenshtein distance between a and b.
    """

    arr1 = a.split("-")
    arr2 = b.split("-")

    l1 = len(arr1)
    l2 = len(arr2)

    dist = [[0 for j in range(l2 + 1)] for i in range(l1 + 1)]

    dist[0][0] = 0

    for i in range(1, l1 + 1):
        dist[i][0] = i
    for i in range(1, l2 + 1):
        dist[0][i] = i

    for i in range(1, l1 + 1):
        for j in range(1, l2 + 1):
            temp = 0 if arr1[i - 1] == arr2[j - 1] else 1
            dist[i][j] = min(dist[i - 1][j] + 1, dist[i][j - 1] + 1,
                             dist[i - 1][j - 1] + temp)

    ldist = float(dist[l1][l2]) / max(l1, l2)

    return ldist
