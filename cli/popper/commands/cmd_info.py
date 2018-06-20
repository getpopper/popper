import os
import click
import popper.utils as pu
import requests
from popper.cli import pass_context
from io import BytesIO

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
@click.argument('pipeline', required=True)
@pass_context
def cli(ctx, pipeline):
    """Displays the information related to a pipeline.
    It gives details about the pipeline name, version,
    and contents of the pipeline.

    Examples:
      popper info popperized/quiho-popper/single-node
    """
    pipeline = pipeline.split('/')
    # checking the validity of the provided arguments
    if len(pipeline) != 3:
        pu.fail("Bad pipeline name. See 'popper info --help' for more info.")

    get_info(pipeline)


def get_info(pipeline):
    """Prints the information about the specified pipeline.

    Args:
        pipeline (list): [org,repo,pipeline_name]
    """

    # Checking if the popperized repositories are present or not
    info = {}
    org = pipeline[0]
    repo = pipeline[1]
    pipe = pipeline[2]

    commit_url = 'https://api.github.com/repos'
    commit_url += '/{}/{}/git/refs/heads/master'.format(org, repo)

    r = pu.make_gh_request(
        commit_url,
        msg="Please check if the specified pipeline exists "
        "and the internet is connected."
    )

    r = r.json()
    info['name'] = pipe
    info['url'] = 'https://github.com/{}/{}'.format(org, repo)
    info['sha'] = r['object']['sha']

    temp = {}
    contents = " ".join(pu.read_gh_pipeline(org, repo, pipe)[1:])
    """
    readme_url = "https://raw.githubusercontent.com"
    readme_url += "/{}/{}/master".format(org, repo)
    readme_url += "/pipelines/{}/README.md".format(pipe)

    r = pu.make_gh_request(readme_url, err=False)
    content = ""
    if r.status_code != 200:
        pass
    else:
        # str functions take different number of arguments in python 2/3
        try:
            content = str(BytesIO(r.content).getvalue(), 'utf-8')
        except TypeError:
            content = str(BytesIO(r.content).getvalue()).encode("utf-8")

        content = "\n".join(content.split("\n")[1:])
    """

    if len(contents) != 0:
        temp['description'] = contents

    pu.print_yaml(info)
    if 'description' in temp:
        pu.print_yaml(temp)
