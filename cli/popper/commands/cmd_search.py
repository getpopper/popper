import click
import os
import glob
import popper.utils as pu
from popper.cli import pass_context
import yaml


@click.command('search', short_help='Used to search for an experiment in your pipeline folder')
@click.argument('repository', required=False)
@pass_context
def cli(ctx, repository):
    """Searches the pipeline folder for the specified experiment and returns the path 
    if the experiment is present.
    
    Example:

    popper search exp1 #Searches for exp1 in pipeline folder
    exp1 found at path ./pipelines/exp1
    """

    project_root = pu.get_project_root()

    popperized_path = os.path.join(project_root,'popperized')

    config = pu.read_config()

    if !config['popperized']:
        pu.fail("No popperized repositories have been added")

    if repository in config['popperized']:
        repo_folder = repository.replace('/','_',-1)
        repo_path = os.path.join(popperized_path,repo_folder)
        get_repository(repo_path)
    else:
        search_repositories(config, popperized_path)

def search_repositories(config, popperized_path):
    if config['popperized']:
        repositories = config['popperized']
        for repo in repositories:
            repo_folder = repo.replace('/','_',-1)
            repo_path = os.path.join(popperized_path,repo_folder)
            get_repository(repo_path)
    else:
        pu.info("There are no repositories to check", fg="yellow", bold=True)


def get_repository(repo_path):
    config_filename = os.path.join(repo_path, '.popper.yml')
    with open(config_filename, 'r') as f:
        config = yaml.load(f.read())

    pu.print_yaml(config['metadata'])

