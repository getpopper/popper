import click
import popper.utils as pu
import requests
import os
from popper.cli import pass_context


@click.command('info', short_help='Shows the information about a pipeline')
@click.argument('query', required=True)
@pass_context
def cli(ctx, query):
    """Displays the information related to a pipeline.
    It gives details about the pipeline name, version,
    and contents of the pipeline.

    Examples:
      popper info popperized/quiho-popper/single-node
    """
    query = query.split('/')
    get_info(query)


def get_info(query):
    config = pu.read_config()
    if 'popperized' not in config:
        pu.fail('No popperized repositories present.')

    popperized_repos = config['popperized']

    if 'github/' + "/".join(query[:-1]) not in popperized_repos:
        pu.fail("Repository not found.")

    info = {}
    repo_name = "/".join(query[:-1])
    pipeline_name = query[-1]
    org_path = os.path.join(pu.get_project_root(), 'org')
    pipeline_path = os.path.join(org_path, "/".join(query[1:]))

    commit_url = 'https://api.github.com/repos/'+ repo_name + '/commits'
    commits = requests.get(commit_url).json()

    info['Github Url'] = 'https://github.com/' + "/".join(query[1:])
    info['Pipeline name'] = pipeline_name
    info['Version'] = commits[0]['sha']

    try:
        content = ''
        with open(os.path.join(pipeline_path, 'README'), 'r') as f:
            content = f.read()

        info['README'] = content
    except FileNotFoundError :
        pass

    pu.print_yaml(info, fg='yellow')
