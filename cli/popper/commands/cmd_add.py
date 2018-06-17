#!/usr/bin/env python

import click
import os
import requests
import popper.utils as pu
import shutil
import yaml
import tarfile
from io import BytesIO
from popper.cli import pass_context
import urllib


@click.command(
    'add',
    short_help='Add a pipeline from popperized repositories on github.'
)
@click.argument('pipeline', required=True)
@click.option(
    '--folder',
    help='Folder where the new pipeline will be'
    'stored, relative to project root.',
    show_default=True,
    default='pipelines'
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
        pu.fail("Bad pipeline name. See 'popper add --help' for more info.")

    owner, repo, pipe_name = pipeline.split('/')

    config = pu.read_config()

    if pipe_name in config['pipelines']:
        pu.fail("Pipeline {} already in repo.".format(pipe_name))

    project_root = pu.get_project_root()
    pipelines_dir = os.path.join(project_root, folder)

    if not os.path.exists(pipelines_dir):
        os.mkdir(pipelines_dir)

    gh_url = 'https://github.com/{}/{}/'.format(owner, repo)
    gh_url += 'archive/{}.tar.gz'.format(branch)

    pu.info("Downloading pipeline {}... ".format(pipe_name))

    r = requests.get(gh_url, stream=True)
    if r.status_code != 200:
        pu.fail("Unable to feth the pipeline. Please check if the name" +
                " of the pipline is correct and the internet is connected")

    file_name = gh_url.split('/')[-1]
    base_name = os.path.basename(gh_url)
    with open(file_name, 'wb') as f:
        shutil.copyfileobj(r.raw, f)

    tar = tarfile.open(file_name)
    tar.extractall(pipe_name)
    tar.close()

    os.remove(file_name)

    os.rename('{}/{}-{}/pipelines/{}'.format(
        pipe_name, repo, branch, pipe_name), os.path.join(folder, pipe_name))
    shutil.rmtree('{}'.format(pipe_name))

    pu.info("Updating popper configuration... ")

    repo_config = get_config(owner, repo)

    config['pipelines'][pipe_name] = repo_config['pipelines'][pipe_name]
    config['pipelines'][pipe_name]['path'] = os.path.join(folder, pipe_name)

    pu.write_config(config)

    pu.info("Pipeline {} has been added successfully.".format(pipe_name),
            fg="green")


def get_config(owner, repo):
    """It returns the content of the .popper.yml file of the repository
    whose pipeline we are copying.
    """

    yaml_url = 'https://raw.githubusercontent.com/{}/{}/{}/.popper.yml'.format(
        owner, repo, 'master')

    r = requests.get(yaml_url)
    config = yaml.load(r.content)

    return config
