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
from errno import EACCES, EPERM, ENOENT


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
    repositories on github. The pipeline argument is provided as owner/repo/
    pipeline. For example, 'popper add popperized/quiho-popper/single-node'
    adds the 'single-node' pipeline from the 'quiho-popper' repository from the
    'popperized' organization.
    """
    if len(pipeline.split('/')) != 3:
        raise BadArgumentUsage(
            "Bad pipeline name. See 'popper add --help' for more info.")

    owner, repo, pipe_name = pipeline.split('/')

    if folder:
        path, basename = os.path.split(folder)
        if not basename:  # Only true when trailing slash is present
            path, basename = os.path.split(path)
        if basename:
            new_pipe_name = basename  # Use basename as the name of pipeline
        else:
            pu.fail("The path is invalid.")
    else:  # If no pipeline name is provided, use the original pipeline name
        new_pipe_name = pipe_name

    config = pu.read_config()

    if new_pipe_name in config['pipelines']:
        pu.fail("Pipeline {} already in repo.".format(new_pipe_name))

    project_root = pu.get_project_root()

    if not folder:  # Put it in the pipelines directory, default case
        folder = os.path.join('pipelines', new_pipe_name)
    elif '/' not in folder:  # Put it in the path inside pipelines directory
        folder = os.path.join('pipelines', folder)

    pipelines_dir = os.path.join(project_root, folder)

    # Remove the trailing slash, is present
    folder = folder[:-1] if folder[-1] == '/' else folder

    create_path(pipelines_dir)

    gh_url = 'https://github.com/{}/{}/'.format(owner, repo)
    gh_url += 'archive/{}.tar.gz'.format(branch)

    pu.info("Downloading pipeline {}... ".format(pipe_name))

    r = pu.make_gh_request(
        gh_url,
        msg="Unable to fetch the pipeline. Please check if the name"
        " of the pipeline is correct and the internet is connected"
    )

    # Downloading and extracting the tarfile
    with tarfile.open(mode='r:gz', fileobj=BytesIO(r.content)) as t:
        t.extractall()

    try:
        os.rename('{}-{}/pipelines/{}'.format(
            repo, branch, pipe_name), pipelines_dir)
    except OSError:
        pu.fail("Make sure the path is empty.")
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

    # r = requests.get(yaml_url)
    r = pu.make_gh_request(yaml_url)
    config = yaml.load(r.content)

    return config


def create_path(path):
    """Recursively creates path if it does not exist."""

    if not os.path.exists(path):
        try:
            os.mkdir(path)
        except (OSError, IOError) as e:
            if e.errno == EPERM or e.errno == EACCES:
                pu.fail(
                    "Could not create the necessary path.\n"
                    "Please make sure you have the correct permissions."
                )
            elif e.errno == ENOENT:
                create_path(os.path.join(os.path.split(path)[0]))
                os.mkdir(path)
            else:
                pu.fail("Failed due to unknown reasons.")
