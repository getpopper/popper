#!/usr/bin/env python

import click
import os
import requests
import popper.utils as pu
import yaml
import zipfile
from zipfile import BadZipfile
from io import BytesIO
from popper.cli import pass_context


@click.command(
    'add',
    short_help='Add a pipeline from popperized repositories on github.'
)
@click.argument('pipeline', required=True)
@pass_context
def cli(ctx, pipeline):
    """Add a pipeline to your repository from the existing popperized
    repositories on github. The pipeline argument is provided as owner/repo/
    pipeline. For example, popper add popperized/quiho-popper/single-node
    adds the single-node pipeline from the quiho-popper repository.
    """
    try:
        owner, repo, pipeline_name = pipeline.split('/')
    except ValueError:
        pu.fail("See popper add --help for more info.")

    project_root = pu.get_project_root()

    pipelines_dir = os.path.join(project_root, 'pipelines')
    if os.path.exists(pipelines_dir):
        pass
    else:
        os.chdir(project_root)
        os.mkdir('pipelines')

    pipeline_path = os.path.join(pipelines_dir, pipeline_name)
    os.chdir(pipelines_dir)
    os.mkdir(pipeline_name)
    os.chdir(pipeline_path)

    pipeline_url = 'https://github.com/{}/{}/tree/master/pipelines/{}' \
        .format(owner, repo, pipeline_name)
    download_url = 'https://github-download-only-a-folder.glitch.me/dl?url={}'\
        .format(pipeline_url)

    pu.info("Downloading pipeline {} ... ".format(pipeline_name))
    r = requests.get(download_url)
    if r.status_code == 200:
        try:
            z = zipfile.ZipFile(BytesIO(r.content))
            z.extractall()
        except BadZipfile:
            z.close()
    else:
        pu.fail("Unable to fetch the pipeline. Please check if the name" +
                " of the pipeline is correct and the internet is connected")
    pu.info("Updating the configuration ... ")
    repo_config = get_config(owner, repo)
    update_config(owner, repo, pipeline_name, pipeline_path, repo_config)

    pu.info("Pipeline {} has been added successfully.".format(pipeline_name)
            + " It can be viewed in the pipelines directory.",
            fg="green")


def get_config(owner, repo):
    """It returns the content of the .popper.yml file of the repository
    whose pipeline we are copying.
    """

    yaml_url = 'https://raw.githubusercontent.com' \
        + '/{}/{}/master/.popper.yml'.format(owner, repo)

    r = requests.get(yaml_url)
    config = yaml.load(r.content)

    return config


def update_config(owner, repo, pipeline_name, path, repo_config):
    """Adds the information about the added pipeline in the
    popperized entry of the .popper.yml file.
    """
    pipeline_path = 'pipelines/{}'.format(pipeline_name)

    if 'stages' in repo_config:
        pipeline_stages = repo_config['stages'][pipeline_name]
    else:
        pipeline_stages = [
            'setup.sh',
            'run.sh',
            'post-run.sh',
            'validate.sh',
            'teardown.sh']

    pipeline_envs = []
    if 'envs' in repo_config:
        pipeline_envs = repo_config['envs'][pipeline_name]

    source_url = 'github.com/{}/{}'.format(owner, repo)
    config = pu.read_config()
    config['pipelines'][pipeline_name] = {
        'envs': pipeline_envs,
        'path': pipeline_path,
        'stages': pipeline_stages,
        'source': source_url
    }

    if 'stages' not in config:
        config['stages'] = {}

    config['stages'][pipeline_name] = pipeline_stages

    if 'envs' not in config:
        config['envs'] = {}

    config['envs'][pipeline_name] = pipeline_envs

    if 'popperized' not in config:
        config['popperized'] = []
    config['popperized'].append('github/{}/{}'.format(owner, repo))

    pu.write_config(config)
