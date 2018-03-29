#!/usr/bin/env python

import click
import popper.utils as pu

from popper.cli import pass_context

@click.command(
    'stages', short_help='See and manipulate stages of a pipeline.'
)
@click.argument('pipeline', required=True)
@click.option(
    '--set',
    help='Provide comma separated list of stages to set the stages of a '
         'pipeline. Without the --replace flag, the stages are added alongwith '
         'the existing stages, otherwise they are replaced.',
    required=False,
)
@click.option(
    '--replace',
    is_flag=True,
    help='Use alongwith the --set option to overwrite the curent stages.',
    required=False,
)
@pass_context
def cli(ctx, pipeline, set, replace):
    """View or change the stages of a pipeline.
    """
    config = pu.read_config()
    if pipeline in config['pipelines']:
        if set:
            if replace:
                config['pipelines'][pipeline]['stages'] = set.split(',')
            else:
                for stage in set.split(','):
                    if stage not in config['pipelines'][pipeline]['stages']:
                        config['pipelines'][pipeline]['stages'].append(stage)
            pu.write_config(config)
        pu.info("\nStages:", fg="yellow")
        pu.print_yaml(config['pipelines'][pipeline]['stages'], fg="white")
    else:
        pu.fail("The pipeline {} is not defined. \nSee popper.yml file to see "
                "which pipelines are defined.".format(pipeline))
