import os
import click
import shutil
import popper.utils as pu
from popper.cli import pass_context


@click.command('mv', short_help='Rename or move a pipeline.')
@click.argument('cur', required=True)
@click.argument('new', required=True)
@pass_context
def cli(ctx, cur, new):
    """Used to rename a popper pipeline

    Examples:

    popper mv exp1 experiment1

    popper mv pipelines1/exp1 pipelines2/exp1

    This will rename the pipeline exp1 to experiment1
    """

    popper_config = pu.read_config()
    data = {}

    cur_path, new_path = False, False

    if '/' in cur:
        data['cur_name'] = cur.split('/')[-1]
        data['cur_path'] = cur
    else:
        data['cur_name'] = cur

    if '/' in new:
        data['new_name'] = new.split('/')[-1]
        data['new_path'] = "/".join(new.split('/')[:-1])
    else:
        data['new_name'] = new

    rename(data)


def rename(data):
    """Method to rename or move a pipeline from one directory to another

    Args:
        data (dict): Contains the input details of the arguments given by the
                     user. It has the following keys :

                     cur_name (str): the current name of the pipeline
                     new_name (str): the new name for the pipeline
                     cur_path (str): the current relative path of the pipeline
                     new_path (str): the new relative path for the pipeline

    """

    cur_name = data['cur_name']
    project_root = pu.get_project_root()
    popper_config = pu.read_config()
    pipelines = popper_config['pipelines']
    new_name = data['new_name']

    if cur_name in pipelines:

        if 'cur_path' in data:

            if not pipelines[cur_name]['path'] == data['cur_path']:
                pu.fail(
                    "No pipeline {} exists at {}.".format(
                        cur_name, data['cur_path'])
                )
        else:
            data['cur_path'] = pipelines[cur_name]['path']

        pipelines[new_name] = pipelines.pop(cur_name)
        abs_path_old = os.path.join(project_root, data['cur_path'])

        if 'new_path' in data:
            abs_path_new = os.path.join(project_root, data['new_path'])
        else:
            data['new_path'] = "/".join(data['cur_path'].split('/')[:-1])
            abs_path_new = os.path.join(project_root, data['new_path'])

        data['new_path'] = os.path.join(data['new_path'], data['new_name'])

        if os.path.exists(abs_path_new):
            abs_path_new = os.path.join(abs_path_new, data['new_name'])
            os.rename(abs_path_old, abs_path_new)
        else:
            os.makedirs(abs_path_new)
            shutil.move(abs_path_old, abs_path_new)

            if data['cur_name'] != data['new_name']:
                temp_path = os.path.join(abs_path_new, data['cur_name'])
                abs_path_new = os.path.join(abs_path_new, data['new_name'])
                os.rename(temp_path, abs_path_new)

            abs_path_old = "/".join(abs_path_old.split("/")[:-1])
            if os.listdir(abs_path_old) == []:
                shutil.rmtree(abs_path_old)

        pipelines[new_name]['path'] = data['new_path']
        popper_config['pipelines'] = pipelines

        pu.write_config(popper_config)

    else:
        pu.fail("Pipeline {} doesn't exists".format(cur_name))
