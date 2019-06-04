import os
import sys
import base64
import threading
from collections import defaultdict

import yaml
import click
import requests

from popper.cli import log

if os.environ.get('XDG_CACHE_HOME', None):
    CACHE_FILE = os.path.join(
        os.environ['XDG_CACHE_HOME'], '.popper_cache.yml')
else:
    CACHE_FILE = os.path.join(
        os.environ['HOME'], '.cache', '.popper_cache.yml')


def decode(line):
    """Make treatment of stdout Python 2/3 compatible"""
    if isinstance(line, bytes):
        return line.decode('utf-8')
    return line


def get_items(dict_object):
    """Python 2/3 compatible way of iterating over a dictionary"""
    for key in dict_object:
        yield key, dict_object[key]


class threadsafe_iter_3:
    """Takes an iterator/generator and makes it thread-safe by
    serializing call to the `next` method of given iterator/generator.
    """

    def __init__(self, it):
        self.it = it
        self.lock = threading.Lock()

    def __iter__(self):
        return self

    def __next__(self):
        with self.lock:
            return self.it.__next__()


class threadsafe_iter_2:
    """Takes an iterator/generator and makes it thread-safe by
    serializing call to the `next` method of given iterator/generator.
    """

    def __init__(self, it):
        self.it = it
        self.lock = threading.Lock()

    def __iter__(self):
        return self

    def next(self):
        with self.lock:
            return self.it.next()


def threadsafe_generator(f):
    """A decorator that takes a generator function and makes it thread-safe.
    """
    def g(*args, **kwargs):
        if sys.version_info[0] < 3:
            return threadsafe_iter_2(f(*args, **kwargs))
        else:
            return threadsafe_iter_3(f(*args, **kwargs))
    return g


def find_default_wfile(wfile):
    """
    Used to find `main.workflow` in $PWD or in `.github`
    And returns error if not found

    Returns:
        path of wfile
    """
    if not wfile:
        if os.path.isfile("main.workflow"):
            wfile = "main.workflow"
        elif os.path.isfile(".github/main.workflow"):
            wfile = ".github/main.workflow"

    if not wfile:
        log.fail(
            "Files {} or {} not found.".format("./main.workflow",
                                               ".github/main.workflow"))
    if not os.path.isfile(wfile):
        log.fail("File {} not found.".format(wfile))
        exit(1)

    return wfile


def find_recursive_wfile():
    """
    Used to search for `.workflow` files in $PWD and
    then recursively in sub directories

    Returns:
        list of path of workflow files
    """
    wfile_list = list()
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.workflow'):
                wfile = os.path.join(root, file)
                wfile = os.path.abspath(wfile)
                wfile_list.append(wfile)
    return wfile_list


def get_gh_headers():
    """Method for  getting the headers required for making authorized
    GitHub API requests.
    Returns:
        headers (dict): a dictionary representing HTTP-headers and their
        values.
    """
    gh_token = os.environ.get('POPPER_GITHUB_API_TOKEN', None)

    headers = {}

    if gh_token:
        headers = {
            'Authorization': 'token ' + gh_token
        }

    return headers


def make_gh_request(url, err=True, msg=None):
    """Method for making GET requests to GitHub API
    Args:
        url (str): URL on which the API request is to be made.
        err (bool): Checks if an error message needs to be printed or not.
        msg (str): Error message to be printed for a failed request.
    Returns:
        Response object: contains a server's response to an HTTP request.
    """
    if not msg:
        msg = (
            "Unable to connect. If your network is working properly, you might"
            " have reached Github's API request limit. Try adding a Github API"
            " token to the 'POPPER_GITHUB_API_TOKEN' variable."
        )

    response = requests.get(url, headers=get_gh_headers())
    if err and response.status_code != 200:
        log.fail(msg)
    else:
        return response


def read_search_sources():
    """This function fetches the list of orgs from where to
    search the action repos.
    """
    base_dir = os.path.dirname(__file__)
    with open(os.path.join(
            base_dir, 'resources/.search_sources.yml'), 'r') as sf:
        search_sources = yaml.load(sf, Loader=yaml.FullLoader)

    return search_sources


def fetch_metadata(update_cache):
    """Fetch metatdata of the repositories from the
    search_sources on which to run the search.

    Args:
        update_cache (bool) : Flag variable to decide whether to update
        the cache or not.

    Returns:
        dict : All metadata related to the actions.
    """
    update = False
    if (not os.path.isfile(CACHE_FILE)) or update_cache:
        update = True

    if not update:
        # Use metadata from cache and skip its update.
        if not os.path.isfile(CACHE_FILE):
            log.fail('Metadata cache does not exist.')

        with open(CACHE_FILE, 'r') as cf:
            metadata = yaml.load(cf, Loader=yaml.FullLoader)

    else:
        # Update the cache file.
        log.info('Updating action metadata cache...\n')
        search_sources = read_search_sources()
        source_list = []
        for org in search_sources:
            for repo in repos_in_org(org):
                source_list.append((org, repo))

        metadata = defaultdict(dict)
        with click.progressbar(
                source_list,
                show_eta=False,
                bar_template='[%(bar)s] %(info)s | %(label)s',
                show_percent=True) as bar:
            for r in bar:
                org, repo = r[0], r[1]
                bar.label = "Fetching action metadata from '{}/{}'".format(
                    org, repo)
                metadata[org][repo] = fetch_repo_metadata(org, repo)

        with open(CACHE_FILE, 'w') as cf:
            yaml.dump(dict(metadata), cf)

    return metadata


def fetch_repo_metadata(org, repo):
    """Returns the metadata for a repo.

    Args:
        org (str) : The github organisation name.
        repo (str) : The repository name.

    Returns:
        dict : Metadata of the repo.
    """
    readme = fetch_readme_for_repo(org, repo)
    meta = dict()
    if readme:
        meta['repo_readme'] = readme
    else:
        meta['repo_readme'] = ""
    return meta


def fetch_readme_for_repo(org, repo):
    """Method to fetch the README for the repo
    if present.

    Args:
        org (str) : The github organisation name.
        repo (str) : The repository name.

    Returns:
        str : The contents of the README file.

    """
    r = make_gh_request(
        'https://api.github.com/repos/{}/{}/readme'
        .format(org, repo), err=False
    ).json()

    if r.get('content', None):
        return base64.b64decode(r['content']).decode('utf-8')


def repos_in_org(org):
    """Fetch the list of repos in a Github org.

    Args:
        org (str) : The org whose repo list is needed.

    Returns:
        list : List of repos in the org.
    """
    result = list()
    r = make_gh_request('https://api.github.com/users/{}/repos'.format(org))
    for repo in r.json():
        result.append(repo['name'])
    return result
