#!/usr/bin/env python

import click
import os
import sys
import shutil
import popper.utils as pu

from popper.cli import pass_context


@click.command(
    'reset', short_help='Delete all pipelines in the project.'
)
@pass_context
def cli(ctx):
    """Resets a popper repository completely, removing all existing
    pipelines and folders, leaving behind a newly created .popper.yml file.
    """

    if(not click.confirm("This will remove all the pipeline files in this project,"
        " do you want to continue?", abort=False)):
        sys.exit(0)

    git_files = pu.get_git_files()

    project_root = pu.get_project_root()

    for file_name in git_files:
        file_path = os.path.join(project_root, file_name)
        try:
            shutil.rmtree(file_path)
        except OSError:
            os.remove(file_path)

    delete_empty_folders(project_root, git_files)

    config = {
        'metadata': {
            'access_right': "open",
            'license': "CC-BY-4.0",
            'upload_type': "publication",
            'publication_type': "article"
        },
        'pipelines': {},
        'popperized': [
            "github/popperized"
        ]
    }

    pu.write_config(config)

    with open(os.path.join(project_root, '.gitignore'), 'a') as f:
        f.write('.cache\n')
        f.write('popper_logs\n')
        f.write('popper_status\n')

    pu.info("Reset complete", fg="cyan")


def delete_empty_folders(root, files):
    """Used to delete empty folders after all the git tracked files are
    deleted.

    Args:
        root (str): The path of the project root of the repository.
        files (list): The list of git tracked files.
    """

    folders = set([])
    for f in files:
        f = f.split("/")
        if "." not in f[0]:
            folders.add(f[0])

    for folder in folders:
        folder_path = os.path.join(root, folder)
        shutil.rmtree(folder_path)
