import click
import popper.utils as pu
import popper.scm as scm
from popper.gha import Workflow
from popper.cli import pass_context


@click.command('add', short_help='Import workflow from remote repo.')
@click.argument('path', required=True)
@pass_context
def cli(ctx, path):
    """Imports a workflow from a remote project to the current project
    directory.
    """
    project_root = scm.get_popper_root_folder()
    try:
        Workflow.import_from_repo(path, project_root)
    except Exception:
        pu.fail('Failed to import from {} !'.format(path))
