import os

import click
import hcl
import popper.utils as pu
from ..cli import pass_context
import types


@click.argument(
    'wfile', required=True)
@click.command('dot', short_help='Generates a dot file [Used for graphical representations]')
@pass_context
def cli(ctx, wfile):
    """Creates a dot file"""
    if not os.path.isfile(wfile):
        pu.fail("File {} not found.\n".format(wfile))
        exit(1)

    with open(wfile, 'r') as fp:
        wf = hcl.load(fp)

    graph = "digraph G {\n"
    name = list(wf["workflow"].keys())[0]
    pu.info("Dot file for %s workflow\n" % name)
    pu.info("`ascii.dot` created\n\n")

    action = wf["workflow"][name]["resolves"]
    parent_action = cur_action = action

    if not isinstance(cur_action, str):
        cur_action = cur_action[0]

    graph = add(parent_action, cur_action, wf["action"], graph) + "}\n"

    with open('ascii.dot', 'w') as fp:
        fp.write(graph)

    os.system("awk '!seen[$0]++' ascii.dot > out")

    pu.info(graph)


# Recursively go through "needs" and add corresponding actions to graph
def add(parent_action, cur_action, actions, graph):

    if 'needs' in actions[cur_action]:
        action_list = actions[cur_action]['needs']

        if isinstance(action_list, str):
            parent_action = action_list
            graph = add(cur_action, parent_action, actions, graph)
        else:
            for act in action_list:
                graph = add(cur_action, act, actions, graph)

    # Adds edges to the graph
    # Graph::Easy can't work with '-' in names
    # Graph::Easy separates a single string with n-1 ' ' into n different words
    if cur_action != parent_action:
        graph += "\t{} -> {};\n".format(
            parent_action.replace(' ', '_').replace('-', '_'),
            cur_action.replace(' ', '_').replace('-', '_'))

    return graph
