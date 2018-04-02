#!/usr/bin/env python

import click
import os
import requests
import popper.utils as pu
import yaml
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
    if os.path.exists(path):
        pass
    else:
        os.chdir(project_root)
        os.mkdir('pipelines')

    dirname = pipeline_name
    url = ('https://api.github.com/repos/{}/{}/contents/pipelines/{}'
           .format(owner, repo, pipeline_name))

    repo_config = get_config(owner, repo)

    save_directory(path, dirname, url)
    path = os.path.join(path, pipeline_name)
    update_config(owner, repo, pipeline_name, path, repo_config)
    pu.info("Pipeline {} successfully added.".format(pipeline_name)
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


def save_directory(path, dirname, url, topmost=1):
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
    if topmost == 1:
        # Progressbar to show the number of files installed.
        with click.progressbar(response,
                               show_eta=False,
                               label='Downloading pipeline files:',
                               item_show_func=lambda i: ''
                               + '| Current File/Directory > '
                               + i['name'] if i else None,
                               bar_template='[%(bar)s] %(label)s | %(info)s',
                               show_percent=True) as bar:

            for item in bar:
                save_directory_util(path, dirname, url, item)
    else:
        for item in response:
            save_directory_util(path, dirname, url, item)


def save_directory_util(path, dirname, url, item):
    """A utility function that recursively calls the save_directory
    and save_file function as per the requirements."""
    if item['type'] == 'file':
        filename = item['name']
        download_url = item['download_url']
        filepath = item['path']
        save_file(path, filename, download_url)
    else:
        dirname = item['name']
        url = item['url']
        dirpath = item['path']
        save_directory(path, dirname, url, 0)


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
