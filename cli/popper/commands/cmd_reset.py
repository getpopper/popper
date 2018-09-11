#!/usr/bin/env python

import click
import os
import sys
import popper.utils as pu
import popper.template as pt
from popper.cli import pass_context


@click.command(
    'reset', short_help='Delete all pipelines in the project.'
)
@pass_context
def cli(ctx):
    """Resets a popper repository completely, removing all existing
    pipelines and folders, leaving behind a newly created .popper.yml file.

    Note: It only removes those files inside a pipeline folder that are also
    tracked by git. Untracked files will not be deleted.
    """
    msg = (
        "This will remove all the pipeline files in this "
        " project, do you want to continue?"
    )
    if(not click.confirm(msg, abort=False)):
        sys.exit(0)

    project_root = pu.get_project_root()

    if project_root != os.getcwd():
        msg = 'This command can only be executed from the project root folder'
        pu.fail(msg)

    config = pu.read_config()

    for _, p in config['pipelines'].items():
        pu.exec_cmd('git rm -r {}'.format(p['path']))
    pu.write_config(pu.init_config)
    content = pt.ReadMe()
    content.init_project()
    pu.info("Reset complete", fg="cyan")
