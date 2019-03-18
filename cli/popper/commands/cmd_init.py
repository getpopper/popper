import click
import os
import git
import popper.utils as pu
from popper.cli import pass_context


@click.command('init', short_help='Initialize a Popper project.')
@pass_context
def cli(ctx):
    """Initializes a repository by creating the .popper.yml file.
    """
    try:
        repo = git.Repo(search_parent_directories=True)
    except git.exc.InvalidGitRepositoryError:
        pu.fail('Must be a git repository ! \n')

    project_root = repo.git.rev_parse('--show-toplevel')

    if pu.is_popperized():
        pu.fail('Repository has already been popperized')
        return

    pu.write_config(pu.init_config)

    with open(os.path.join(project_root, '.gitignore'), 'a') as f:
        f.write(pu.gitignore_content)

    # write README
    pu.info('Popperized repository {}\n'.format(project_root))
