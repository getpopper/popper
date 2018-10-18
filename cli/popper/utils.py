import click
import os
import sys
import yaml
import requests
import subprocess

from collections import defaultdict

noalias_dumper = yaml.dumper.SafeDumper
noalias_dumper.ignore_aliases = lambda self, data: True

init_config = {
    'metadata': {
        'access_right': "open",
        'license': "CC-BY-4.0",
        'upload_type': "publication",
        'publication_type': "article"
    },
    'pipelines': {},
    'search_sources': [
        "popperized"
    ],
    'badge-server-url': 'http://badges.falsifiable.us',
    'version': 1,
}

gitignore_content = ".pipeline_cache\npopper/\n"


def get_items(dict_object):
    """Python 2/3 compatible way of iterating over a dictionary"""
    for key in dict_object:
        yield key, dict_object[key]


def get_path_to_config():
    """Obtains the path to the config file.

    Returns:
        path (str): string containing path to where config file is stored.
    """

    project_root = get_project_root()
    config_path = os.path.join(project_root, '.popper.yml')

    if os.path.isfile(config_path):
        return os.getcwd()

    return ""


def get_search_sources(config):
    if 'search_sources' not in config and 'popperized' not in config:
        return []
    if 'search_sources' in config:
        return config['search_sources']
    if 'popperized' in config:
        return config['popperized']


def fetch_pipeline_metadata(skip_update=False):
    meta = defaultdict(dict)
    repos = []

    project_root = get_project_root()
    cache_file = os.path.join(project_root, '.pipeline_cache.yml')

    if not skip_update:
        config = read_config()

        sources = get_search_sources(config)

        info('Updating pipeline metadata cache\n')

        for s in sources:
            if '/' in s:
                repos.append(s)
            else:
                for repo in repos_in_org(s):
                    repos.append(s+'/'+repo)

        with click.progressbar(
                repos,
                show_eta=False,
                bar_template='[%(bar)s] %(info)s | %(label)s',
                show_percent=True) as bar:
            for r in bar:
                bar.label = "Fetching pipeline metadata from '{}'".format(r)
                fetch_metadata_for_repo(r, meta)

        with open(cache_file, 'w') as f:
            yaml.dump(dict(meta), f)
    else:
        if not os.path.isfile(cache_file):
            fail("Metadata cache doesn't exist. Use --help for more.")

        with open(cache_file, 'r') as f:
            meta = yaml.load(f)

    return meta


def fetch_metadata_for_repo(orgrepo, meta):
    org, repo = orgrepo.split('/')
    config = read_config_remote(org, repo)

    if not config or 'pipelines' not in config:
        return

    meta[org][repo] = config

    fetch_readmes(meta, org, repo)


def fetch_readmes(meta, org, repo):
    pipelines = meta[org][repo]['pipelines']
    for name, pipe in pipelines.items():
        url = "https://raw.githubusercontent.com/{}/{}/{}/{}/README.md".format(
            org, repo, 'master', pipe['path']
        )
        r = make_gh_request(url, err=False)

        readme = ''
        if r.status_code == 200:
            readme = r.content.decode("utf-8")
        pipe['readme'] = readme


def get_project_root():
    """Tries to find the root of the project with the following heuristic:

      - Find the .git folder in cwd

    Returns:
        project_root (str): The fully qualified path to the root of project.
    """
    base = exec_cmd('git rev-parse --show-toplevel', ignoreerror=True)

    if not base:
        fail("Unable to find root of project. Initialize repository first.")

    return base


def read_config(name=None):
    """Reads config from .popper.yml file.

    Args:
        name (default=None): Name of a pipeline, whose config is to be returned

    Returns:
        If name is not provided:
            config (dict): dictionary representing the YAML file contents.
        If name is provided:
            Two-tuple consisting of config (dict) and pipeline_config (dict) :
            dictionary representing the pipeline configuration
    """
    config_filename = os.path.join(get_project_root(), '.popper.yml')

    if not os.path.isfile(config_filename):
        fail(".popper.yml file doesn't exist. See 'popper init --help'.")

    with open(config_filename, 'r') as f:
        config = yaml.load(f.read())
        if not config:
            fail(".popper.yml is empty. Consider deleting it and "
                 "reinitializing the repo. See popper init --help for more.")
        for key in ["metadata", "pipelines"]:
            if key not in config:
                fail(".popper.yml doesn't contain expected entries. "
                     "Consider deleting it and reinitializing the repo. "
                     "See popper init --help for more.")

    if 'version' not in config:
        warn("No 'version' element found in .popper.yml file. Assuming 1.")
        config['version'] = 1

    if not name:
        return config
    else:
        pipeline_config = config['pipelines'].get(name, None)
        if not pipeline_config:
            fail("Pipeline {} does not exist.".format(name))
        return config, pipeline_config


def write_config(config):
    """Writes config to .popper.yml file."""
    config_filename = os.path.join(get_project_root(), '.popper.yml')

    with open(config_filename, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, Dumper=noalias_dumper)


def is_popperized():
    """Determines if the current repo has already been popperized by checking
    whether the '.popper.yml' file on the root of the project exits.

    Returns:
       True if the '.popper.yml' exists, False otherwise.
    """
    config_filename = os.path.join(get_project_root(), '.popper.yml')
    return os.path.isfile(config_filename)


def update_config(name, stages='', envs={}, parameters=[], reqs={},
                  relative_path='', timeout=None):
    """Updates the configuration for a pipeline."""

    config = read_config()
    if config['pipelines'].get(name, None):
        if not stages:
            stages = ','.join(config['pipelines'][name]['stages'])
        if not envs:
            envs = config['pipelines'][name].get('envs', {})
        if not relative_path:
            relative_path = config['pipelines'][name]['path']
        if not reqs:
            reqs = config['pipelines'][name].get('requirements', {})
        if timeout is None:
            timeout = config['pipelines'][name].get('timeout')

    if name == 'paper':
        stages = 'build'

    config['pipelines'][name] = {
        'stages': stages.split(','),
        'envs': envs,
        'parameters': parameters,
        'requirements': reqs,
        'path': relative_path,
    }

    if timeout is not None:
        config['pipelines'][name]['timeout'] = timeout

    write_config(config)


def get_filename(abs_path, stage):
    """Returns filename for a stage"""
    os.chdir(abs_path)
    if os.path.isfile(stage):
        return stage
    elif os.path.isfile(stage + '.sh'):
        return stage + '.sh'
    else:
        return None


def fail(msg):
    """Prints the error message on the terminal."""
    click.secho('ERROR: ' + msg, fg='red', bold=True, err=True)
    sys.exit(1)


def warn(msg):
    click.secho('WARNING: ' + msg, bold=True, fg='red', err=True)


def info(msg, **styles):
    """Prints the message on the terminal."""
    click.secho(msg, **styles)


def print_yaml(msg, **styles):
    """Prints the messages in YAML's block format. """
    click.secho(yaml.safe_dump(msg, default_flow_style=False), **styles)


def parse_timeout(timeout):
    """Takes timeout as string and parses it to obtain the number of seconds.
    Generates valid error if proper format is not used.

    Returns:
        Value of timeout in seconds (float).
    """
    time_out = 0
    to_seconds = {"s": 1, "m": 60, "h": 3600}
    try:
        time_out = float(timeout)
    except ValueError:
        literals = timeout.split()
        for literal in literals:
            unit = literal[-1].lower()
            try:
                value = float(literal[:-1])
            except ValueError:
                fail("invalid timeout format used. "
                     "See popper run --help for more.")
            try:
                time_out += value * to_seconds[unit]
            except KeyError:
                fail("invalid timeout format used. "
                     "See popper run --help for more.")

    return time_out


def get_remote_url():
    """Python 2/3 comptatible method for getting the remote origin url

    Returns:
        string - url of remote origin,
            For example: https://github.com/systemslab/popper
    """
    repo_url = exec_cmd('git config --get remote.origin.url', ignoreerror=True)

    # cleanup the URL so we get in in https form and without '.git' ending
    if repo_url.endswith('.git'):
        repo_url = repo_url[:-4]
    if 'git@' in repo_url:
        repo_url = 'https://' + repo_url[4:].replace(':', '/')

    return repo_url


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
        fail(msg)
    else:
        return response


def read_config_remote(org, repo, branch='master'):
    url = "https://raw.githubusercontent.com/{}/{}/{}/.popper.yml".format(
        org, repo, branch
    )
    r = make_gh_request(url, err=False)

    if r.status_code != 200:
        return None

    try:
        config = yaml.load(r.content.decode("utf-8"))
    except Exception:
        return None

    if type(config) != dict:
        return None

    if 'version' not in config:
        config['version'] = 1

    return config


def repos_in_org(org):
    r = make_gh_request('https://api.github.com/users/{}/repos'.format(org))
    for repo in r.json():
        yield repo['name']


def get_head_commit():
    return exec_cmd('git rev-parse HEAD')[:-1]


def is_repo_empty():

    p = subprocess.Popen(['git', 'rev-parse', 'HEAD'],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p.communicate()
    if p.returncode != 0:
        return True
    return False


def in_pipeline(name=False):
    """Checks if the current working directory is a pipeline
    or not.

    Args:
        name (bool): Set as True if the user wants the name of the pipeline.

    Returns:
        pipeline_name (str): The name of the current pipeline. Returned iff
        the argument `name` is set to True.

        True/False (bool): True if the user is inside a pipeline. False
        otherwise. Returned iff the argument `name` is set to False.
    """

    cwd = os.getcwd()
    pipeline_name = os.path.basename(cwd)
    pipelines = read_config()['pipelines']

    if pipeline_name in pipelines:
        pipeline = pipelines[pipeline_name]
        rel_path = os.path.relpath(cwd, get_project_root())

        if rel_path == pipeline['path']:
            if name:
                return pipeline_name
            else:
                return True

    if name:
        return None
    else:
        return False


def get_name_and_path_for_new_pipeline(folder, pipeline_name=''):
    """Returns name and path when a new pipeline is added or initialized

    When a new pipeline is added the name and path is decided from the
    argument provided. When a / is in the name, we treat the string as a path.
    If <name> is a string without /, then put it in the pipelines/ folder. If
    it does contains a /, then treat it as a path, where the last component of
    the path (i.e. the basename of the string) is the name of the pipeline and
    the preceding substring is the folder.

    Arguments:
        folder (string) -- Path/name of new pipeline provided as argument to
            popper init or popper add commands

    Keyword Arguments:
        pipeline_name (string) -- In case path is None, name of the new
        pipeline needs to be provided, which is the same as that of the added
        pipline for popper add. Not applicable for popper init (default: {''})

    Returns:
        pipeline_name (string) -- New pipeline name

        path (string) -- New pipeline path, relative to the project root
    """
    if folder:
        path, basename = os.path.split(folder)
        if not basename:  # Only true when trailing slash is present
            path, basename = os.path.split(path)
        new_pipeline_name = basename

        if '/' in folder:
            path = folder
            if folder[-1] == '/':  # Remove the traoling slash if present
                path = folder[:-1]
        else:
            path = os.path.join('pipelines', basename)

    else:  # If no path is provided, use the original pipeline name
        path = os.path.join('pipelines', pipeline_name)
        new_pipeline_name = pipeline_name

    return new_pipeline_name, path


def exec_cmd(cmd, ignoreerror=False):
    try:
        output = subprocess.check_output(cmd, shell=True).strip()
    except subprocess.CalledProcessError as ex:
        if ignoreerror:
            return ''
        fail("Command '{}' failed: {}".format(cmd, ex))

    output = output.decode('utf-8')

    return output


def infer_repo_name_from_root_folder():
    """Finds the root folder of a local Github repository and returns it.

    Returns:
        repo_name (str): the name of the root folder.
    """
    root_folder = get_project_root()
    repo_name = os.path.basename(root_folder)
    return repo_name


def get_git_files():
    """Used to return a list of files that are being tracked by
    git.

    Returns:
        files (list) : list of git tracked files
    """
    gitfiles = exec_cmd("git ls-files")
    return gitfiles.split("\n")
