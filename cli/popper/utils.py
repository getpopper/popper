import click
import os
import sys
from ruamel import yaml


def get_path_to_config():
    """Obtains the path to the config file.

    Returns:
        path (str): string containing path to where config file is stored.
    """
    if os.path.isfile('.popper.yml'):
        return os.getcwd()

    if os.path.isfile(os.path.join('..', '..', '.popper.yml')):
        return os.path.join(os.getcwd(), '..', '..')

    return ""


def get_project_root():
    """Tries to find the root of the project with the following heuristic:

      - Find the .popper.yml file in cwd or two folders up
      - Find the .git folder in cwd

    Returns:
        project_root (str): The fully qualified path to the root of project.
    """
    path_to_config = get_path_to_config()

    if path_to_config:
        return path_to_config

    if os.path.isdir('.git'):
        return os.getcwd()

    fail(
        "Unable to find the root of your project. Initialize repository first."
    )


def read_config():
    """Reads config from .popper.yml file.

    Returns:
        config (dict): dictionary representing the YAML file contents.
    """
    config_filename = os.path.join(get_project_root(), '.popper.yml')

    if not os.path.isfile(config_filename):
        fail(".popper.yml file doesn't exist. See 'popper init --help'.")

    with open(config_filename, 'r') as f:
        config = yaml.safe_load(f.read())
        if not config:
            fail(".popper.yml is empty. Consider deleting it and "
                 "reinitializing the repo. See popper init --help for more.")
        for key in ["metadata", "pipelines"]:
            if key not in config:
                fail(".popper.yml doesn't contain expected entries. "
                     "Consider deleting it and reinitializing the repo. "
                     "See popper init --help for more.")

    return config


def write_config(config):
    """Writes config to .popper.yml file."""
    config_filename = os.path.join(get_project_root(), '.popper.yml')

    with open(config_filename, 'w') as f:
        yaml.safe_dump(config, f, default_flow_style=False)


def is_popperized():
    """Determines if the current repo has already been popperized by checking
    whether the '.popper.yml' file on the root of the project exits.

    Returns:
       True if the '.popper.yml' exists, False otherwise.
    """
    config_filename = os.path.join(get_project_root(), '.popper.yml')
    return os.path.isfile(config_filename)


def update_config(name, stages, envs, relative_path):
    """Updates the configuration for a pipeline"""

    if name == 'paper':
        stages = 'build'

    config = read_config()
    config['pipelines'][name] = {
        'stages': stages.split(','),
        'envs': envs.split(','),
        'path': relative_path
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
    click.secho('ERROR: ' + msg, fg='red', blink=True, bold=True)
    sys.exit(1)


def warn(msg):
    click.secho('WARNING: ' + msg, fg='magenta', bold=True)


def info(msg, **styles):
    """Prints the message on the terminal."""
    click.secho(msg, **styles)


def print_yaml(msg, **styles):
    """Prints the messages in YAML's block format. """
    click.secho(yaml.dump(msg, default_flow_style=False), **styles)


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
