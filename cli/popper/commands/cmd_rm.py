import os
import click
import shutil
import popper.utils as pu
from popper.cli import pass_context


@click.command('rm', short_help='Remove a pipeline from the project.')
@click.argument('pipeline', required=True)
@pass_context
def cli(ctx, pipeline):
    """Remove a popper pipeline from the user's repository effectively
    to keep the pipelines folder and the .popper.yml files in sync.
    """

    project_root = pu.get_project_root()
    pipeline_dir = project_root

    pipelines = pu.read_config()['pipelines']

    if pipeline in pipelines:
        path = pipelines[pipeline]['path']
        pipeline_dir = os.path.join(
                pipeline_dir,
                path)

    if os.path.isdir(pipeline_dir):

        shutil.rmtree(pipeline_dir)

        popper_config = pu.read_config()
        del popper_config['pipelines'][pipeline]

        pu.info("Pipeline {} removed successfully".format(pipeline),
                fg="green")

        pu.write_config(popper_config)

    else:
        pu.fail("Pipeline {} doesn't exists".format(pipeline))
