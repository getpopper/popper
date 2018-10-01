#!/usr/bin/env python

import click
import os
import popper.utils as pu
import shutil
import yaml
import tarfile
from io import BytesIO

from popper.cli import pass_context
from popper.exceptions import BadArgumentUsage
from requests.exceptions import ConnectionError


@click.command(
    'add',
    short_help='Add a pipeline from popperized repositories on github.'
)
@click.argument('pipeline', required=True)
@click.argument(
    'folder',
    required=False
)
@click.option(
    '--branch',
    help='To specify the branch of the repository from where the'
    ' popperized pipeline needs to be added. For example: popper '
    'add popperized/swc-lesson-pipelines/co2-emissions --branch test.',
    required=False,
    show_default=True,
    default="master",
)
@pass_context
def cli(ctx, pipeline, folder, branch):
    """Add a pipeline to your repository from the existing popperized
    repositories on github. The pipeline argument is provided as
    <org>/<repo>/<pipeline>. For example:

      popper add popperized/quiho-popper/single-node

    The above adds the 'single-node' pipeline from the 'quiho-popper'
    repository from the 'popperized' organization.

    This commands makes use of Github's API, which has a limit on the number of
    requests per hour that an unauthenticated user can make. If you reach this
    limit, you can provide a Github API token via a POPPER_GITHUB_API_TOKEN
    environment variable. If defined, this variable is used to obtain the token
    when executing HTTP requests.
    """
    if len(pipeline.split('/')) != 3:
        raise BadArgumentUsage(
            "Bad pipeline name. See 'popper add --help' for more info.")

    owner, repo, pipe_name = pipeline.split('/')

    new_pipe_name, folder = pu.get_name_and_path_for_new_pipeline(
        folder, pipe_name)

    config = pu.read_config()

    if new_pipe_name in config['pipelines']:
        pu.fail("Pipeline {} already in repo.".format(new_pipe_name))

    project_root = pu.get_project_root()

    pipelines_dir = os.path.join(project_root, folder)

    gh_url = 'https://github.com/{}/{}/'.format(owner, repo)
    gh_url += 'archive/{}.tar.gz'.format(branch)

    pu.info(
        "Downloading pipeline {} as {}...".format(pipe_name, new_pipe_name)
    )

    try:
        # Downloading and extracting the tarfile
        r = pu.make_gh_request(
            gh_url,
            msg="Unable to fetch the pipeline. Please check if the name"
            " of the pipeline is correct and the internet is connected"
        )
        with tarfile.open(mode='r:gz', fileobj=BytesIO(r.content)) as t:
            t.extractall()

        if not os.path.exists(pipelines_dir):
            try:
                os.makedirs(pipelines_dir)
            except (OSError, IOError):
                pu.fail("Could not create the necessary path.\n")
        elif len(os.listdir(pipelines_dir)) != 0:
            pu.fail("The path already exists and is not empty.")

    except ConnectionError:
        pu.fail("Could not download the pipeline due to Connection Error")

    try:
        os.rename('{}-{}/pipelines/{}'.format(
            repo, branch, pipe_name), pipelines_dir)
    except OSError:
        pu.fail(
            "Could not rename {} to {}.".format(
                '{}-{}/pipelines/{}'.format(repo, branch, pipe_name),
                pipelines_dir
            )
        )
    finally:
        shutil.rmtree('{}-{}'.format(repo, branch))

    pu.info("Updating popper configuration... ")

    repo_config = get_config(owner, repo)

    config['pipelines'][new_pipe_name] = repo_config['pipelines'][pipe_name]
    config['pipelines'][new_pipe_name]['path'] = folder

    pu.write_config(config)
    pu.info(
        "Pipeline {} has been added successfully.".format(new_pipe_name),
        fg="green"
    )


def get_config(owner, repo):
    """It returns the content of the .popper.yml file of the repository
    whose pipeline we are copying.

    Args:
        owner (str): The username of the owner of the repository
        repo  (str): The name of the repository from where the
                     pipeline is being added
    Returns:
        config (dict): .popper.yml configuarion of the pipeline
    """

    yaml_url = 'https://raw.githubusercontent.com/{}/{}/{}/.popper.yml'.format(
        owner, repo, 'master')

    r = pu.make_gh_request(yaml_url)
    config = yaml.load(r.content)

    return config
