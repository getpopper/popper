import click
import popper.utils as pu

from popper.cli import pass_context
from popper.exceptions import UsageError


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
    """Add or remove environment variables defined for matrix execution of
    a pipeline."""

    config, pipeline_config = pu.read_config(pipeline)

    if add and rm:
        raise UsageError("Both add and rm cannot be given at the same time. "
                         "See popper env-vars --help for more information.")

    if add:
        env_vars = pipeline_config.get('vars', [])
        vars_add = {}
        for var in add:
            key, val = var.split('=')
            vars_add[key] = val
        env_vars.append(vars_add)
        pu.update_config(pipeline, vars=env_vars)

    elif rm:
        env_vars = pipeline_config.get('vars', None)
        if not env_vars:
            pu.fail("No environment variables defined for this pipeline.")

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

        if index != -1:
            env_vars.pop(index)
            pu.update_config(pipeline, vars=env_vars)
        else:
            pu.fail("The environment variable list does "
                    "not exist for this pipeline.")

    else:
        try:
            env_vars = pipeline_config['vars']
            if len(env_vars) == 0:
                raise KeyError
            pu.print_yaml(env_vars)
        except KeyError:
            pu.info("No environment variables defined for this pipeline.")
