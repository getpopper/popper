#!/usr/bin/env python

import click
import popper.utils as pu

from popper.cli import pass_context


@click.command(
    'stages', short_help='See and manipulate stages of a pipeline.'
)
@click.argument('pipeline', required=False)
@click.option(
    '--set',
    help='Comma separated list of stages in the pipeline.',
    required=False,
)
@pass_context
def cli(ctx, pipeline, set):
    """View or change the stages of a pipeline.
    """

    if not pipeline:
        get_pipe = pu.in_pipeline(name=True)
        if get_pipe is not None:
            pipeline = get_pipe
        else:
            pu.fail("This is not a pipeline")

    config = pu.read_config()
    if pipeline in config['pipelines']:
        if set:
            config['pipelines'][pipeline]['stages'] = set.split(',')
            pu.write_config(config)
        pu.info("\nStages:", fg="yellow")
        pu.print_yaml(config['pipelines'][pipeline]['stages'], fg="white")
    else:
        pu.fail("The pipeline {} is not defined. \nSee popper.yml file to see "
                "which pipelines are defined.".format(pipeline))
