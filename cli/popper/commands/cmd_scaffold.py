import os
import click
import popper.utils as pu
import popper.scm as scm
from popper.cli import pass_context


@click.command('scaffold', short_help='Scaffolds a workflow folder.')
@pass_context
def cli(ctx):
    """Scaffolds a workflow.
    """
    if not pu.is_popperized():
        pu.fail('Repository has not been popperized')
        return

    project_root = scm.get_root_folder()
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
        pass
    
    with open(os.path.join(actions_dir, 'example/entrypoint.sh'), 'w') as ef:
        pass

    with open(os.path.join(actions_dir, 'example/README.md'), 'w') as rf:
        pass
    
    pu.info('Successfully scaffolded. \n')
