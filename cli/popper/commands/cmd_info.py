import os
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
    # checking the validity of the provided arguments
    if len(query) != 3:
        pu.fail("Bad pipeline name. See 'popper info --help' for more info.")

    get_info(query)


def get_info(query):
    # Checking if the popperized repositories are present or not
    info = {}
    org = query[0]
    repo = query[1]
    pipe = query[2]

    # check if the github personal access token has been specified by the user
    POPPER_GITHUB_API_TOKEN = ""
    if 'POPPER_GITHUB_API_TOKEN' in os.environ:
        POPPER_GITHUB_API_TOKEN = os.environ['POPPER_GITHUB_API_TOKEN']

    headers = {}

    if POPPER_GITHUB_API_TOKEN != "":
        headers = {
            'Authorization': 'token %s' % POPPER_GITHUB_API_TOKEN
        }

    commit_url = 'https://api.github.com/repos'
    commit_url += '/{}/{}/git/refs/heads/master'.format(org, repo)

    r = requests.get(commit_url, headers=headers)

    if r.status_code == 200:
        r = r.json()
        info['name'] = pipe
        info['url'] = 'https://github.com/{}/{}'.format(org, repo)
        info['sha'] = r['object']['sha']
        pu.print_yaml(info)
    else:
        pu.fail("Please check if the specified pipeline exists " +
                " and the internet is connected")
