import os
import click
import popper.utils as pu
from popper.cli import pass_context
import git


@click.command('scaffold', short_help='Scaffolds a workflow folder.')
@pass_context
def cli(ctx):
    """Scaffolds a workflow.
    """
    if not pu.is_popperized():
        pu.fail('Repository has not been popperized')
        return
    
    try:
        repo = git.Repo(search_parent_directories=True)
    except git.exc.InvalidGitRepositoryError:
        pu.fail('Must be a git repository ! \n')
    
    project_root = repo.git.rev_parse('--show-toplevel')

    curr_dir = os.getcwd()
    actions_dir = os.path.join(curr_dir, 'actions')

    for filename in os.listdir(project_root):
        if filename.endswith('.workflow'):
            pu.fail('.workflow file already present !')

    if not os.path.exists(actions_dir):
        os.mkdir(actions_dir)
        os.mkdir(os.path.join(actions_dir, 'example'))
    else:
        if not os.path.exists(os.path.join(actions_dir, 'example')):
            os.mkdir(os.path.join(actions_dir, 'example'))

    # Generate actions files
    with open(os.path.join(project_root, 'main.workflow'), 'w') as f:
        f.write(pu.main_workflow_content % os.path.relpath(
            os.path.join(actions_dir, 'example'), project_root)
        )

    with open(os.path.join(actions_dir, 'example/Dockerfile'), 'w') as df:
        df.write(pu.dockerfile_content)

    with open(os.path.join(actions_dir, 'example/entrypoint.sh'), 'w') as ef:
        ef.write(pu.entrypoint_content)

    with open(os.path.join(actions_dir, 'example/README.md'), 'w') as rf:
        rf.write(pu.readme_content)

    pu.info('Successfully scaffolded. \n')
