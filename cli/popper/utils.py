import click
import os
import sys
import yaml


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
        config = yaml.load(f.read())

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
    config = read_config()
    config['pipelines'][name] = {
        'stages': stages.split(','),
        'envs': envs.split(','),
        'path': relative_path
    }
    write_config(config)


def fail(msg):
    click.echo('ERROR: ' + msg)
    sys.exit(1)


def info(msg):
    click.echo(msg)
