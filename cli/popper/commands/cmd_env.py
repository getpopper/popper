import click
import popper.utils as pu

from popper.cli import pass_context


@click.command('env', short_help='Modify environments for a pipeline.')
@click.argument('pipeline', required=True)
@click.option(
    '--add',
    help="Comma-separated list of environments to add.",
    required=False
)
@click.option(
    '--rm',
    help="Comma-separated list of environments to remove",
    required=False
)
@pass_context
def cli(ctx, pipeline, add, rm):
    """Manipulates the environments that are associated to a pipeline. An
    environment is a docker image where a pipeline runs when 'popper run' is
    executed. The 'host' environment is a special case that corresponds to
    the running directly on the environment where the 'popper' command runs,
    i.e. running directly on the host without docker. When a new pipeline is
    created using, the default environment is 'host' (see 'popper init --help'
    for more).

    Examples:

      popper env mypipeline # show environments for pipeline

      popper env mypipeline --add ubuntu-xenial,centos-7.2

      popper env mypipeline --rm host
    """
    config = pu.read_config()

    if not add and not rm:
        pu.info(str(config['pipelines'][pipeline]['envs']))

    if add:
        config['pipelines'][pipeline]['envs'] += add.split(',')

    if rm:
        for e in rm.split(','):
            config['pipelines'][pipeline]['envs'].remove(e)

    pu.write_config(config)
