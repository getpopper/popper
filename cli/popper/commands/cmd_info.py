import click
import popper.utils as pu
import requests
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
    info = {}
    org = query[0]
    repo = query[1]
    pipe = query[2]

    commit_url = 'https://api.github.com/repos/{}/{}/commits'.format(org, repo)
    r = requests.get(commit_url)

    if r.status_code == 200:
        commits = r.json()
        info['name'] = pipe
        info['url'] = 'https://github.com/{}/{}'.format(org, repo)
        if len(commits) > 0 and isinstance(commits[0], type({})):
            info['version'] = commits[0].get('sha')

        pu.print_yaml(info)
    else:
        pu.fail("Please check if the specified pipeline exists " +
                " and the internet is connected")
