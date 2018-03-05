import click
import os
import glob
import popper.utils as pu
from popper.cli import pass_context

@click.command('search', short_help='Used to search for an experiment in your pipeline folder')
@click.argument('experiment', required=True)
@pass_context
def cli(ctx, experiment):
    """Searches the pipeline folder for the specified experiment and returns the path 
    if the experiment is present.
    
    Example:

    popper search exp1 #Searches for exp1 in pipeline folder
    exp1 found at path ./pipelines/exp1
    """

    project_root = pu.get_project_root()
    pipeline_path = os.path.join(project_root, 'pipelines')

    search_experiments(pipeline_path, experiment)

def search_experiments(pipeline_path, experiment):
    result = glob.glob(os.path.join(pipeline_path, experiment))
    if result:    
        pu.info(experiment + ' found at path :- '+result[0])
    else:
        pu.fail(experiment + ' not found')


