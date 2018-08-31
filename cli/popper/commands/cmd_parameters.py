import click
import popper.utils as pu
import sys

from popper.cli import pass_context
from popper.exceptions import UsageError


@click.command('parameters', short_help='Parametrize a pipeline pipeline.')
@click.argument('pipeline', required=False)
@click.option(
    '--add',
    multiple=True,
    help='Add a set of environment variables in the form of key=value',
    required=False
)
@click.option(
    '--rm',
    multiple=True,
    help='Remove a set of environment variable in the form of key=value',
    required=False
)
@pass_context
def cli(ctx, pipeline, add, rm):
    """Define or remove executions of a pipeline."""

    if not pipeline:
        get_pipe = pu.in_pipeline(name=True)
        if get_pipe is not None:
            pipeline = get_pipe
        else:
            pu.fail("This is not a pipeline")

    config, pipeline_config = pu.read_config(pipeline)

    if add and rm:
        raise UsageError("Both add and rm cannot be given at the same time. "
                         "See popper env-vars --help for more information.")

    if add:
        env_vars = pipeline_config.get('parameters', [])
        vars_add = {}
        for var in add:
            key, val = var.split('=')
            vars_add[key] = val
        env_vars.append(vars_add)
        pu.update_config(pipeline, parameters=env_vars)
        sys.exit(0)

    if rm:
        env_vars = pipeline_config.get('parameters', None)

        if not env_vars:
            pu.fail("No parameters defined for this pipeline.")

        vars_del = {}
        for var in rm:
            key, val = var.split('=')
            vars_del[key] = val

        index = -1
        for vars in env_vars:
            if len(vars.keys()) != len(vars_del.keys()):
                continue
            else:
                successful = True
                for key in vars_del:
                    if vars[key] != vars_del[key]:
                        successful = False
                if successful:
                    index = env_vars.index(vars)
                    break

        if index == -1:
            pu.fail("Unable to find this parametrization in this pipeline.")

        env_vars.pop(index)
        pu.update_config(pipeline, parameters=env_vars)
        sys.exit(0)

    try:
        env_vars = pipeline_config['parameters']
        if len(env_vars) == 0:
            raise KeyError
        pu.print_yaml(env_vars)
    except KeyError:
        pu.info("No parameterization defined for this pipeline.")
