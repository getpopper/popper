import os
import re
import sys
import threading
from builtins import str

import yaml
import click
import requests

from popper.cli import log
from popper import scm


def setup_cache():
    """Set up popper cache file path.
    """
    xdg_cache_dir = os.environ.get(
        'XDG_CACHE_HOME', os.path.join(os.environ['HOME'], '.cache'))
    if not os.path.isdir(xdg_cache_dir):
        os.makedirs(xdg_cache_dir)
    return os.path.join(xdg_cache_dir, '.popper_cache.yml')


def decode(line):
    """Make treatment of stdout Python 2/3 compatible."""
    if isinstance(line, bytes):
        return line.decode('utf-8')
    return line


def get_items(dict_object):
    """Python 2/3 compatible way of iterating over a dictionary."""
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


def find_default_wfile(wfile=None):
    """
    Used to find `main.workflow` in $PWD or in `.github`
    And returns error if not found.

    Args:
        wfile (str): The path to a workflow file.
        The default value of this is None, when the
        function searches for `main.workflow` or
        `.github/main.workflow'.

    Returns:
        str: Path of wfile.
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

    return wfile


def find_recursive_wfile():
    """
    Used to search for `.workflow` files in $PWD and
    then recursively in sub directories.

    Returns:
        list: List of path of workflow files.
    """
    wfile_list = list()
    for root, _, files in os.walk('.'):
        for file in files:
            if file.endswith('.workflow'):
                wfile = os.path.join(root, file)
                wfile = os.path.abspath(wfile)
                wfile_list.append(wfile)
    return wfile_list


def make_gh_request(url, err=True, msg=None):
    """Method for making GET requests to GitHub API.
    Args:
        url (str): URL on which the API request is to be made.
        err (bool): Checks if an error message needs to be printed or not.
        msg (str): Error message to be printed for a failed request.
    Returns:
        Response object: Contains a server's response to an HTTP request.
    """
    if not msg:
        msg = (
            "Unable to connect. Please check your network connection."
        )

    response = requests.get(url)
    if err and response.status_code != 200:
        log.fail(msg)
    else:
        return response


def read_search_sources():
    """Method to fetch the list of actions.

    Returns:
        list: The list of actions.
    """
    response = make_gh_request(
        'https://raw.githubusercontent.com/systemslab/popper/'
        'master/cli/resources/search_sources.yml')

    return yaml.load(response.text, Loader=yaml.FullLoader)


def fetch_metadata(update_cache=False):
    """Fetch metatdata of the repositories from the
    search_sources on which to run the search.

    Args:
        update_cache (bool): Flag variable to decide whether to update
        the cache or not.

    Returns:
        dict: All metadata related to the actions.
    """
    cache_file = setup_cache()

    update = False
    if (not os.path.isfile(cache_file)) or update_cache:
        update = True

    if not update:
        # Use metadata from cache and skip its update.
        with open(cache_file, 'r') as cf:
            metadata = yaml.load(cf, Loader=yaml.FullLoader)

    else:
        # Update the cache file.
        log.info('Updating action metadata cache...\n')
        search_sources = read_search_sources()

        source_list = list()
        for url in search_sources:
            _, _, user, repo, path_to_action, version = scm.parse(url)
            source_list.append((user, repo, path_to_action, version))

        metadata = dict()
        with click.progressbar(
                source_list,
                show_eta=False,
                bar_template='[%(bar)s] %(info)s | %(label)s',
                show_percent=True,
                width=30) as bar:
            for r in bar:
                user, repo, path_to_action, version = r[0], r[1], r[2], r[3]
                action = os.path.normpath(
                    os.path.join(user, repo, path_to_action))
                bar.label = "{}".format(action)
                metadata[action] = fetch_repo_metadata(
                    user, repo, path_to_action, version)

        with open(cache_file, 'w') as cf:
            yaml.dump(dict(metadata), cf)

    return metadata


def fetch_repo_metadata(user, repo, path_to_action, version):
    """Returns the metadata for a repo.

    Args:
        user (str): The user to which the actions belongs to.
        repo (str): The parent repository name.
        path_to_action (str): The path to the action from the root.
        version (str): The branch where the action resides.

    Returns:
        dict: Metadata of the repo.
    """
    readme = fetch_readme_for_repo(user, repo, path_to_action, version)
    meta = dict()
    meta['repo_readme'] = readme
    return meta


def fetch_readme_for_repo(user, repo, path_to_action, version=None):
    """Method to fetch the README for the repo
    if present.

    Args:
        user (str): The user to which the actions belongs to.
        repo (str): The parent repository name.
        path_to_action (str): The path to the action from the root.
        version (str): The branch where the action resides.

    Returns:
        str: The contents of the README file.

    """
    if not version:
        version = 'master'
    url = os.path.join('https://raw.githubusercontent.com',
                       user, repo, version, path_to_action, 'README.md')
    r = make_gh_request(url, err=False)
    return r.text


def sanitized_name(name):
    """Clean an action name and change it to
    proper format. It replaces all the unwanted
    characters with `_`.

    Args:
        name (str): The crude action name.

    Returns:
        str: The sanitized action name.
    """
    return re.sub('[^a-zA-Z0-9_.-]', '_', name)


def of_type(param, valid_types):
    """Function to check the type of a parameter.

    It tries to match the type of the parameter with the
    types passed through `valid_types` list.

    Args:
        param: A value of any type.
        valid_types (list): A list of acceptable types.

    Returns:
        bool: True/False, depending upon whether the type of
        the passed param matches with any of the valid types.
    """
    # Python 2/3 compability.
    try:
        basestring
    except BaseException:
        basestring = str

    for t in valid_types:
        if t == 'str':
            if isinstance(param, basestring):
                return True

        if t == 'dict':
            if isinstance(param, dict):
                return True

        if t == 'los':
            if isinstance(param, list):
                res = list(map(lambda a: isinstance(a, basestring), param))
                return False not in res

    return False
