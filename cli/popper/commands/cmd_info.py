import click
import popper.utils as pu
import requests
import os
from popper.cli import pass_context

"""
Making the code compatible with both python 2.x and 3.x environments.
2.x does not have a FileNotFoundError and makes use of IOError to handle
such exceptions.
"""
try:
    FileNotFoundError
except NameError:
    FileNotFoundError = IOError


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
    # Checking if the popperized repositories are present or not
    config = pu.read_config()
    if 'popperized' not in config:
        pu.fail('No popperized repositories present.')

    popperized_repos = config['popperized']

    # Checking if the specified pipeline exists
    if 'github/' + "/".join(query[:-1]) not in popperized_repos:
        pu.fail("Repository not found.")

    info = {}
    repo_name = "/".join(query[:-1])
    pipeline_name = query[-1]
    org_path = os.path.join(pu.get_project_root(), 'org')
    pipeline_path = os.path.join(org_path, "/".join(query[1:]))

    commit_url = 'https://api.github.com/repos/' + repo_name + '/commits'
    r = requests.get(commit_url)

    if r.status_code == 200:
        commits = r.json()
        info['Github Url'] = 'https://github.com/' + "/".join(query[1:])
        info['Pipeline name'] = pipeline_name
        if len(commits) > 0 and isinstance(commits[0], type({})):
            info['Version'] = commits[0].get('sha')
        try:
            content = ''
            with open(os.path.join(pipeline_path, 'README'), 'r') as f:
                content = f.read()

            info['README'] = content
        except FileNotFoundError:
            pass

        pu.print_yaml(info, fg='yellow')
    else:
        pu.fail("Please check if the specified pipeline exists " +
                " and the internet is connected")
