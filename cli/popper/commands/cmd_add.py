import click
import os
import hcl
import shutil
import popper.utils as pu
import popper.scm as scm
from popper.cli import pass_context
from distutils.dir_util import copy_tree


@click.command('add', short_help='Import workflow from remote repo.')
@click.argument('path', required=True)
@click.option(
    '--branch',
    help='Specifies the branch to download from.',
    required=False,
    default='master'
)
@pass_context
def cli(ctx, path, branch):
    """Imports a workflow from a remote project to the current project
    directory. For now it can import workflows only from repos hosted at
    github.com
    """
    project_root = scm.get_root_folder()
    if not pu.is_popperized(project_root):
        pu.fail('Repository has not been popperized.')
        return

    parts = path.split('/')
    parts = list(filter(None, parts))
    if len(parts) < 2:
        pu.fail('Remote url format should be  <repo>[/folder[/wf.workflow]]')

    org = parts[0]
    repo = parts[1]

    cloned_project_dir = os.path.join("/tmp", org, repo)
    scm.clone('https://github.com', org, repo, os.path.dirname(
        cloned_project_dir)
    )

    if len(parts) == 2:
        ptw_one = os.path.join(cloned_project_dir, "main.workflow")
        ptw_two = os.path.join(cloned_project_dir, ".github/main.workflow")
        if os.path.isfile(ptw_one):
            path_to_workflow = ptw_one
        elif os.path.isfile(ptw_two):
            path_to_workflow = ptw_two
        else:
            pu.fail("Unable to find a .workflow file")
    elif len(parts) >= 3:
        path_to_workflow = os.path.join('/tmp', org, repo, '/'.join(parts[2:]))
        if not os.path.basename(path_to_workflow).endswith('.workflow'):
            path_to_workflow = os.path.join(path_to_workflow, 'main.workflow')
        if not os.path.isfile(path_to_workflow):
            pu.fail("Unable to find a .workflow file")

    shutil.copy(path_to_workflow, project_root)
    pu.info("Successfully imported workflow\n".format(path_to_workflow))

    with open(path_to_workflow, 'r') as fp:
        wf = hcl.load(fp)

    action_paths = list()
    if wf.get('action', None):
        for _, a_block in wf['action'].items():
            if a_block['uses'].startswith("./"):
                action_paths.append(a_block['uses'])

    action_paths = set([a.split("/")[1] for a in action_paths])
    for a in action_paths:
        copy_tree(os.path.join(cloned_project_dir, a),
                  os.path.join(project_root, a))
        pu.info("Copied {} to {}...\n".format(os.path.join(
            cloned_project_dir, a), project_root))
