#!/usr/bin/env python

import click
import os
import shutil
import sys
from shutil import copytree
import popper.utils as pu

from popper.cli import pass_context


@click.command(
    'reset', short_help='Resets a popper repository completely.'
)
@pass_context
def cli(ctx):
    """Resets a popper repository completely, removing all the installed
    pipelines and folders leaving behind a newly created .popper.yml file
    """

    project_root = pu.get_project_root()

    for file_name in os.listdir(project_root):
        if file_name in [".git", ".cache"]:
            continue

        file_path = os.path.join(project_root, file_name)
        try:
            shutil.rmtree(file_path)
        except OSError:
            os.remove(file_path)

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
