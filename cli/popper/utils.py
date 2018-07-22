import click
import os
import sys
import yaml
import requests
import subprocess

noalias_dumper = yaml.dumper.SafeDumper
noalias_dumper.ignore_aliases = lambda self, data: True


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


def get_project_root():
    """Tries to find the root of the project with the following heuristic:

      - Find the .git folder in cwd

    Returns:
        project_root (str): The fully qualified path to the root of project.
    """

    try:
        base = subprocess.check_output(
            'git rev-parse --show-toplevel', shell=True
        )
    except subprocess.CalledProcessError:
        fail(
            "Unable to find the root of your project."
            "Initialize repository first."
        )

    return base.decode('utf-8').strip()


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


def update_config(name, stages='', envs='', vars=[], reqs={},
                  relative_path=''):
    """Updates the configuration for a pipeline."""

    config = read_config()
    if config['pipelines'].get(name, None):
        if not stages:
            stages = ','.join(config['pipelines'][name]['stages'])
        if not envs:
            envs = ','.join(config['pipelines'][name]['envs'])
        if not relative_path:
            relative_path = config['pipelines'][name]['path']
        if not reqs:
            reqs = config['pipelines'][name].get('requirements', {})

    if name == 'paper':
        stages = 'build'

    config['pipelines'][name] = {
        'stages': stages.split(','),
        'envs': envs.split(','),
        'vars': vars,
        'requirements': reqs,
        'path': relative_path,
    }
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
    args = ['git', 'config', '--get', 'remote.origin.url']
    p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, error = p.communicate()
    if p.returncode == 0:
        # Remove the .git\n from the end of the url returned by Popen
        try:
            return output.decode()[:-5]  # Python 3 returns bytes
        except AttributeError:
            return output[:-5]
    else:
        return ''


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
        msg = "Unable to connect. Please check your network"
        "and try again."

    response = requests.get(url, headers=get_gh_headers())
    if err and response.status_code != 200:
        fail(msg)
    else:
        return response


def read_gh_pipeline(uname, repo, pipeline, branch="master"):
    """Reads the README.md file of a pipeline and returns its
    contents.

    Args:
        uname (str): User/org_name
        repo (str): Name of the repository
        pipeline (str): Name of the pipeline
        branch (str): Name of the branch

    Returns:
        contents (list): the contents of the README.md file
    """
    url = "https://raw.githubusercontent.com"
    url += "/{}/{}/{}".format(uname, repo, branch)
    url += "/pipelines/{}/README.md".format(pipeline)

    contents = ""
    r = make_gh_request(url, err=False)
    if r.status_code != 200:
        pass
    else:
        contents = r.content.decode("utf-8").split("\n")

    return contents


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
