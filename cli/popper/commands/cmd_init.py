import os
import click
import yaml
from popper import scm
from popper.cli import pass_context
from ..cli import log


@click.command('init', short_help='Initialize a Popper project.')
@pass_context
def cli(ctx):
    """Initializes a repository by creating the .popper.yml file in the current
    folder. This command needs to be executed on the root folder of a Git
    repository.
    """
    project_root = scm.get_git_root_folder()

    if os.getcwd() != project_root:
        log.fail("Could not find a Git repository on current directory.")
        log.fail("Run 'popper init' on the root of your Git repository.")

    config_filename = os.path.join(project_root, '.popper.yml')

    noalias_dumper = yaml.dumper.SafeDumper
    noalias_dumper.ignore_aliases = lambda self, data: True

    init_config = {'version': 2}

    with open(config_filename, 'w') as f:
        yaml.dump(init_config, f, default_flow_style=False,
                  Dumper=noalias_dumper)

    log.info('Initialized Popper repository {}'.format(project_root))
