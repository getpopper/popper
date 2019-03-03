import click
import os
import popper.utils as pu
import popper.scm as scm
from popper.cli import pass_context


@click.command('init', short_help='Initialize a Popper project.')
@pass_context
def cli(ctx):
    """Initializes a repository by creating the .popper.yml file.
    """
    project_root = scm.get_root_folder()

    if pu.is_popperized():
        pu.fail('Repository has already been popperized')
        return

    pu.write_config(pu.init_config)

    with open(os.path.join(project_root, '.gitignore'), 'a') as f:
        f.write(pu.gitignore_content)

    # write README
    pu.info('Popperized repository {}\n'.format(project_root))
