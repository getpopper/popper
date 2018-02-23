import click
import os
import popper.utils as pu

from popper.cli import pass_context
from os.path import isfile, isdir, basename


@click.command('init', short_help='Initialize a Popper repo or pipeline.')
@click.argument('name', required=False)
@click.option(
    '--stages',
    help='Comma-separated list of stage names',
    show_default=True,
    default='setup,run,post-run,validate,teardown'
)
@click.option(
    '--envs',
    help='Comma-separated list of environments to use to run a pipeline',
    show_default=True,
    default='host'
)
@click.option(
    '--existing',
    help=('Treat NAME as a path and define a pipeline by '
          'creating an entry in .popper.yml for this existing folder.'),
    is_flag=True
)
@pass_context
def cli(ctx, name, stages, envs, existing):
    """Initializes a repository or a pipeline. Without an argument, this
    command initializes a popper repository. If an argument is given, a
    pipeline or paper folder is initialized. If the given name is 'paper',
    then a 'paper' folder is created. Otherwise, a pipeline named NAME is
    created and initialized inside the 'pipelines' folder.

    By default, the stages of a pipeline are: setup, run, post-run, validate
    and teardown. To override these, the `--stages` flag can be provided, which
    expects a comma-separated list of stage names.

    If the --existing flag is given, the NAME argument is treated as a path to
    a folder, which is assumed to contain bash scripts. --stages must be given.
    """
    project_root = pu.get_project_root()

    # init repo
    if name is None:
        initialize_repo(project_root)
        return

    if not pu.is_popperized():
        pu.fail("Repository has not been popperized yet. See 'init --help'")

    if isdir(os.path.join(project_root, name)) and existing:
        # existing pipeline
        abs_path = os.path.join(project_root, name)
        relative_path = name
        initialize_existing_pipeline(abs_path, stages, envs)
    else:
        # new pipeline
        abs_path = os.path.join(project_root, 'pipelines', name)
        relative_path = os.path.join('pipelines', name)
        initialize_new_pipeline(abs_path, stages, envs)

    pu.update_config(name, stages, envs, relative_path)

    pu.info('Initialized pipeline ' + name)


def initialize_repo(project_root):
    if pu.is_popperized():
        pu.fail('Repository has already been popperized')

    with open(os.path.join(project_root, '.popper.yml'), 'w') as f:
        f.write('{ metadata: { }, pipelines: { } }\n')

    pu.info('Popperized repository ' + project_root)


def initialize_existing_pipeline(pipeline_path, stages, envs):
    for s in stages.split(','):
        s_filename = os.path.join(pipeline_path, s)
        if not isfile(s_filename) and not isfile(s_filename+'.sh'):
            pu.fail(
                ("Unable to find script for stage '" + s + "'. You might need "
                 "to provide values for the --stages flag. See 'init --help'.")
            )


def initialize_new_pipeline(pipeline_path, stages, envs):

    # create folders
    if isdir(pipeline_path) or isfile(pipeline_path):
        pu.fail('File {} already exits'.format(pipeline_path))
    os.makedirs(pipeline_path)

    # write stage bash scripts
    for s in stages.split(','):
        if not s.endswith('.sh'):
            s = s + '.sh'

        with open(os.path.join(pipeline_path, s), 'w') as f:
            f.write('#!/usr/bin/env bash\n')
            f.write('# [wf] execute {} stage\n'.format(s))
            f.write('\n')
        os.chmod(os.path.join(pipeline_path, s), 0o755)

    # write README
    with open(os.path.join(pipeline_path, 'README'), 'w') as f:
        f.write('# ' + basename(pipeline_path) + '\n')
