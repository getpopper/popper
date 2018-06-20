import click
import popper.utils as pu

from popper.cli import pass_context
from popper.exceptions import BadArgumentUsage


@click.command('matrix', short_help='Define execution matrix for a '
               'pipeline using environment variables.')
@click.argument('pipeline', required=True)
@click.option(
    '--add',
    multiple=True,
    help='Add environment variable in the form key=value',
    required=False
)
@click.option(
    '--rm',
    multiple=True,
    help='Remove environment variable using the key',
    required=False
)
@pass_context
def cli(ctx, pipeline, add, rm):
    try:
        config = pu.read_config()
        pipeline_config = config['pipelines'][pipeline]
    except KeyError:
        raise BadArgumentUsage("Pipeline {} does not exist.".format(pipeline))
    if not add and not rm:
        try:
            pu.print_yaml(pipeline_config['matrix']['vars'])
        except KeyError:
            pu.info("No environment variables defined for this pipeline.")
    if add:
        try:
            matrix = pipeline_config['matrix']
        except KeyError:
            matrix = {'vars': {}}
        for var in add:
            key, val = var.split('=')
            matrix['vars'][key] = val
        config['pipelines'][pipeline]['matrix'] = matrix
        pu.write_config(config)
    if rm:
        try:
            matrix = pipeline_config['matrix']
        except KeyError:
            pu.fail("No environment variables defined for this pipeline.")

        for key in rm:
            try:
                del matrix['vars'][key]
            except KeyError:
                raise BadArgumentUsage("Environment variable {} does not "
                                       "exist in the matrix".format(key))
        config['pipelines'][pipeline]['matrix'] = matrix
        pu.write_config(config)
