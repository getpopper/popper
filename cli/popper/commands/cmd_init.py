import click
import os
import glob
import popper.utils as pu
import popper.template as pt
from popper.exceptions import BadArgumentUsage
from popper.cli import pass_context
from os.path import isfile, isdir, basename


@click.command('init', short_help='Initialize a Popper project or pipeline.')
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
    '--timeout',
    help='Sets the default timeout for the execution of a pipeline. Pipelines'
         'without a set timeout value will default to 10800 seconds of'
         'timeout.',
    required=False
)
@click.option(
    '--existing',
    help=('Treat NAME as a path and define a pipeline by '
          'creating an entry in .popper.yml for this existing folder.'),
    is_flag=True
)
@click.option(
    '--infer-stages',
    help=('Infers the stages of a pipeline from bash script file names.'
          ' Used in conjuction with the --existing flag.'),
    is_flag=True
)
@pass_context
def cli(ctx, name, stages, envs, existing, infer_stages, timeout):
    """Initializes a repository or a pipeline. Without an argument, this
    command initializes a popper repository. If an argument is given, a
    pipeline or paper folder is initialized. If the given name is 'paper',
    then a 'paper' folder is created. Otherwise, a pipeline named NAME is
    created and initialized inside the 'pipelines' folder.

    By default, the stages of a pipeline are: setup, run, post-run, validate
    and teardown. To override these, the `--stages` flag can be provided, which
    expects a comma-separated list of stage names.

    The teardown stage is to be provided at the end if the --stages flag is
    being used.

    If the --existing flag is given, the NAME argument is treated as a path to
    a folder, which is assumed to contain bash scripts. --stages must be given.
    """

    # check if the the teardown stage is the last stage of the pipeline
    if stages and 'teardown' in stages and stages.split(',')[-1] != 'teardown':
        raise BadArgumentUsage(
            '--stages = Teardown should be the last stage.' +
            ' Consider renaming it or putting it at the end.')

    project_root = pu.get_project_root()
    env_list = envs.split(',')
    # init repo
    if name is None:
        if existing:
            raise BadArgumentUsage(
                "Pipeline path not specified. See popper init --help")

        initialize_repo(project_root)
        return

    if not pu.is_popperized():
        pu.fail("Repository has not been popperized yet. See 'init --help'")

    if isdir(os.path.join(project_root, name)) and existing:
        # existing pipeline
        abs_path = os.path.join(project_root, name)
        relative_path = name
        if infer_stages:
            stages = ",".join(map(lambda x: x[:-3],
                                  sorted(glob.glob1(abs_path, '*.sh'))))
            content = pt.ReadMe()
            content.init_pipeline(abs_path, stages, env_list)
        else:
            initialize_existing_pipeline(abs_path, stages, env_list)
        name = os.path.basename(name)
    elif name == 'paper':
        # create a paper pipeline
        abs_path = os.path.join(project_root, 'paper')
        relative_path = os.path.join('paper')
        initialize_paper(abs_path, envs)
    else:
        # new pipeline
        new_name, relative_path = pu.get_name_and_path_for_new_pipeline(name)
        abs_path = os.path.join(project_root, relative_path)
        initialize_new_pipeline(abs_path, stages, env_list)
        name = new_name

    pu.update_config(
        name,
        stages=stages,
        envs={env: {'args': []} for env in envs.split(',')},
        relative_path=relative_path,
        timeout=timeout
    )
    pu.info(
        "Initialized pipeline '{}' at {}".format(name, relative_path),
        fg='blue', bold=True)


def initialize_repo(project_root):
    """This function is used for initializing a popper repository."""
    content = pt.ReadMe()

    if pu.is_popperized():
        pu.fail('Repository has already been popperized')
        return

    pu.write_config(pu.init_config)

    with open(os.path.join(project_root, '.gitignore'), 'a') as f:
        f.write(pu.gitignore_content)

    # write README
    content.init_project()
    pu.info('Popperized repository ' + project_root, fg='blue', bold=True)


def initialize_existing_pipeline(pipeline_path, stages, envs):
    """This function is used for initalizing an existing pipeline."""

    content = pt.ReadMe()

    for s in stages.split(','):
        s_filename = os.path.join(pipeline_path, s)
        if not isfile(s_filename) and not isfile(s_filename + '.sh'):
            pu.fail(
                "Unable to find script for stage '" + s + "'. You might need "
                "to provide values for the --stages flag. See 'init --help'."
            )
    # write README
    content.init_pipeline(pipeline_path, stages, envs)


def initialize_paper(paper_path, envs):
    """This function is used for initializing the special paper pipeline."""

    # create the paper folder
    if isdir(paper_path):
        pu.fail('The paper pipeline already exists')
    os.makedirs(paper_path)

    # write the build.sh bash script
    with open(os.path.join(paper_path, 'build.sh'), 'w') as f:
        f.write('#!/usr/bin/env bash\n')
        f.write('# [wf] execute build stage.')
        f.write('\n')
    os.chmod(os.path.join(paper_path, 'build.sh'), 0o755)

    # write README
    with open(os.path.join(paper_path, 'README.md',), 'w') as f:
        f.write('# ' + basename(paper_path) + '\n')


def initialize_new_pipeline(pipeline_path, stages, envs):
    """This function is used for initalizing a new pipeline."""

    content = pt.ReadMe()

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
            f.write('# [wf] execute {} stage\n'.format(s.replace('.sh', '')))
            f.write('\n')
        os.chmod(os.path.join(pipeline_path, s), 0o755)

    # write README
    content.init_pipeline(pipeline_path, stages, envs)
