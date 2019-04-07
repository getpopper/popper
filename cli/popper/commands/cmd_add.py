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
@pass_context
def cli(ctx, path):
    """Imports a workflow from a remote project to the current project
    directory.
    """
    project_root = scm.get_root_folder()
    if not pu.is_popperized(project_root):
        pu.fail('Repository has not been popperized.')
        return

    parts = pu.get_parts(path)
    if len(parts) < 3:
        pu.fail(
            'Required url format <url>/<user>/<repo>[/folder[/wf.workflow]]')

    url, service, user, repo, _, _, version = pu.parse(path)

    cloned_project_dir = os.path.join("/tmp", service, user, repo)
    scm.clone(url, user, repo, os.path.dirname(
        cloned_project_dir), version
    )

    if len(parts) == 3:
        ptw_one = os.path.join(cloned_project_dir, "main.workflow")
        ptw_two = os.path.join(cloned_project_dir, ".github/main.workflow")
        if os.path.isfile(ptw_one):
            path_to_workflow = ptw_one
        elif os.path.isfile(ptw_two):
            path_to_workflow = ptw_two
        else:
            pu.fail("Unable to find a .workflow file")
    elif len(parts) >= 4:
        path_to_workflow = os.path.join(
            cloned_project_dir, '/'.join(parts[3:])).split("@")[0]
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
