import os
import click
import shutil
import popper.utils as pu
from popper.cli import pass_context


@click.command('rm', short_help='Removes a pipeline effectively')
@click.argument('pipeline', required=True)
@pass_context
def cli(ctx, pipeline):
    """Remove a popper pipeline from the user's repository effectively
    to keep the pipelines folder and the .popper.yml files in sync.
    """

    project_root = pu.get_project_root()

    if pipeline == 'paper':
        pipeline_dir = project_root
    else:
        pipeline_dir = os.path.join(project_root, 'pipelines')

    pipeline_path = os.path.join(pipeline_dir, pipeline)

    if os.path.isdir(pipeline_path):

        shutil.rmtree(pipeline_path)

        popper_config = pu.read_config()
        del popper_config['pipelines'][pipeline]

        pu.info("Pipeline {} removed successfully".format(pipeline),
                fg="green")

        pu.write_config(popper_config)

    else:
        pu.fail("Pipeline {} doesn't exists".format(pipeline))
