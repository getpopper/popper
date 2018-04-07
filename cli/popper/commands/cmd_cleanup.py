#!/usr/bin/env python

import click
import os
import popper.utils as pu

from popper.cli import pass_context


@click.command(
    'cleanup', short_help='Synchronize your pipelines and popper.yml file.'
)
@pass_context
def cli(ctx):
    """Synchronize your pipelines and popper.yml file if any pipeline or stage
    has been deleted.
    """
    pipeline_dir = os.path.join(pu.get_project_root(), 'pipelines')
    popper_config = pu.read_config()
    pipelines = {}

    for pipeline in os.listdir(pipeline_dir):
        envs = popper_config['pipelines'][pipeline]['envs']
        relative_path = popper_config['pipelines'][pipeline]['path']
        defined_stages = popper_config['pipelines'][pipeline]['stages']
        existing_stages = []
        for stage in defined_stages:
            os.chdir(os.path.join(pipeline_dir, pipeline))
            if os.path.exists(stage+'.sh') or os.path.exists(stage):
                existing_stages.append(stage)
        pipelines[pipeline] = {
            'envs': envs,
            'path': relative_path,
            'stages': existing_stages
        }

    popper_config['pipelines'] = pipelines
    pu.write_config(popper_config)

    pu.info("\nYour popper.yml file has been updated! Run git diff to see "
            "the differences.", fg="white")
