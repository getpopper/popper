import click
import os
import popper.utils as pu
from popper.cli import pass_context


@click.command('require', short_help='Declare pipeline execution requirements')
@click.argument('pipeline', required=False)
@click.option('--env', '-e', help='Declare a required environment variable.',
              required=False, multiple=True)
@click.option('--clear', help='Clear the current requirement list',
              is_flag=True)
@pass_context
def cli(ctx, pipeline, env, clear):
    """ Adds pipeline requirements to .popper.yml """

    # try to get pipeline from current directory
    if not pipeline:
        get_pipe = pu.in_pipeline(name=True)
        if get_pipe is not None:
            pipeline = get_pipe
        else:
            pu.fail("No pipeline detected")

    config = pu.read_config()
    if pipeline not in config['pipelines']:
        pu.fail('Pipeline {} does not exist. Check your .popper.yml file.'
                .format(pipeline))

    # merge current requirements
    reqs = config['pipelines'][pipeline].get('requirements', {})

    var_reqs = set([]) if clear else set(reqs.get('vars', []))
    var_reqs |= set(env)
    var_reqs = list(var_reqs)
    reqs['vars'] = var_reqs

    pu.update_config(pipeline, reqs=reqs)
