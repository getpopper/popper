#!/usr/bin/env python

import click
import os
import popper.utils as pu

from popper.cli import pass_context

# For compatibility between python 2.x and 3.x versions
try:
    FileNotFoundError
except NameError:
    FileNotFoundError = IOError

@click.command(
    'cleanup', short_help='Synchronize your pipelines and popper.yml file.'
)
@pass_context
def cli(ctx):
    """Synchronize your pipelines and popper.yml file if any pipeline or stage
    has been deleted.
    """
    #pipeline_dir = os.path.join(pu.get_project_root(), 'pipelines')
    popper_config = pu.read_config()
    project_root = pu.get_project_root()
    pipelines = popper_config['pipelines']
    
    pipeline_folders = []

    # Removing nonexistent pipelines from .popper.yml
    for p in list(pipelines):
        pipeline = pipelines[p]
        
        pipeline_folder = pipeline['path'].split('/')[0]
        pipeline_folders.append(pipeline_folder)
        pipe_path = os.path.join(project_root,pipeline['path'])
        
        if os.path.exists(pipe_path):

            # Synchronizing stages
            stages = pipeline['stages']
            
            for stage in stages:
                stage_path = os.path.join(pipe_path,stage+'.sh')
                if os.path.exists(stage_path):
                    pass
                else:
                    pipeline['stages'].remove(stage)

        else:
            del pipelines[p]

    popper_config['pipelines'] = pipelines
    
    pu.write_config(popper_config)

    pu.info("\nYour popper.yml file has been updated! Run git diff to see "
            "the differences.", fg="white")
