#!/usr/bin/env python

import click
import os
import requests
import popper.utils as pu

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
    path = os.path.join(project_root, 'pipelines')
    dirname = pipeline_name
    url = ('https://api.github.com/repos/{}/{}/contents/pipelines/{}'
           .format(owner, repo, pipeline_name))

    save_directory(path, dirname, url)
    path = os.path.join(path, pipeline_name)
    update_config(pipeline_name, path)
    pu.info("Pipeline {} successfully added.".format(pipeline_name),
            fg="white")


def save_file(path, filename, download_url):
    """Helper method to save a file.
    """
    os.chdir(path)
    r = requests.get(download_url)
    if r.status_code != 200:
        pu.fail("Could not download the file {}. Make sure the file "
                "exists in the pipeline and try again.".format(filename))
    with open(filename, 'wb') as f:
        f.writelines(BytesIO(r.content))


def save_directory(path, dirname, url):
    """Recursive method to handle directory download. Creates the empty
    directory, saves the files that belong to that directory and then calls
    itself for other directories in that directory.
    """
    r = requests.get(url)
    if r.status_code != 200:
        pu.fail("Could not download the directory {}. Make sure the directory "
                "exists in the pipeline and try again.".format(dirname))

    os.chdir(path)
    try:
        os.mkdir(dirname)
    except FileExistsError:
        pass
    path = os.path.join(path, dirname)

    response = r.json()
    for item in response:
        if item['type'] == 'file':
            filename = item['name']
            download_url = item['download_url']
            filepath = item['path']
            pu.info("Saving file {} to {}".format(filename, filepath))
            save_file(path, filename, download_url)
        else:
            dirname = item['name']
            url = item['url']
            dirpath = item['path']
            pu.info("Saving directory {} to {}".format(dirname, dirpath))
            save_directory(path, dirname, url)


def update_config(pipeline_name, path):
    """Adds the metadata for the pipeline to the .popper.yml file.
    """
    config_envs = ['host']
    config_path = 'pipelines/{}'.format(pipeline_name)
    config_stages = ['setup', 'run', 'post-run', 'validate', 'teardown']
    to_remove = []
    files_list = os.listdir(path)

    for stage in config_stages:
        if stage not in files_list and stage + '.sh' not in files_list:
            to_remove.append(stage)
    config_stages = list(filter(lambda x: x not in to_remove, config_stages))

    config = pu.read_config()
    config['pipelines'][pipeline_name] = {
        'envs': config_envs,
        'path': config_path,
        'stages': config_stages
    }
    pu.write_config(config)
