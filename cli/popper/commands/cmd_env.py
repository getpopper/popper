import click
import requests
import popper.utils as pu
import sys

from popper.cli import pass_context


@click.command('env', short_help='Define or remove execution environments of a'
               ' pipeline.')
@click.argument('pipeline', required=False)
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
@click.option(
    '--ls',
    help="Show a list of available execution environments",
    is_flag=True
)
@click.option(
    '--argument',
    '-arg',
    help="Argument given to Docker through Popper",
    required=False,
    multiple=True
)
@pass_context
def cli(ctx, pipeline, add, rm, ls, argument):
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

    :argument Used to pass an argument to Docker through popper.
    Can be given multiple times (Ignored for 'host').

    An example of usage is as follows:

    popper env mypipeline --add debian-9 -arg --runtime=runc -arg --ipc=host

    This will add to the environment 'debian-9' the set of
    arguments runtime=runc and ipc=host.
    """
    config = pu.read_config()

    if ls:
        try:
            response = requests.get(
                "https://hub.docker.com/v2/repositories/"
                "falsifiable/popper/tags")
            environments = []
            for result in response.json()['results']:
                environments.append(result['name'])
            pu.info('environments:')
            pu.print_yaml(environments)

        except requests.exceptions.RequestException as e:
            click.echo(click.style("Error: " + str(e), fg='red'), err=True)

        sys.exit(0)

    if not pipeline:
        get_pipe = pu.in_pipeline(name=True)
        if get_pipe is not None:
            pipeline = get_pipe
        else:
            pu.fail("This is not a pipeline")

    if not add and not rm:

        if pipeline not in config['pipelines']:
            pu.fail("Pipeline '{}' not found in .popper.yml".format(pipeline))

        pu.print_yaml(config['pipelines'][pipeline]['envs'], fg='yellow')
        sys.exit(0)

    envs = config['pipelines'][pipeline]['envs']
    args = set(argument)

    if add:
        elems = add.split(',')
        environments = set(elems) - set(envs)
        envs.update({env: {'args': []} for env in environments})
        for env in elems:
            envs[env]['args'] = args

    if rm:
        for env in rm.split(','):
            if env in envs:
                envs.pop(env)
            else:
                pu.warn('Environment {} not found in {}'.format(env, pipeline))

    config['pipelines'][pipeline]['envs'] = envs
    pu.write_config(config)
