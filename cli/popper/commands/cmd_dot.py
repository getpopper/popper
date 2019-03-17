import os

import click
import hcl
import popper.utils as pu
from ..cli import pass_context
import types


@click.option(
    '--wfile',
    help=(
        'File containing the definition of the workflow. '
        '[default: ./github/main.workflow OR ./main.workflow]'
    ),
    required=False,
    default=None
)
@click.command('dot', short_help='Generates a dot file '
                                 '[Used for graphical representations]')
@pass_context
def cli(ctx, wfile):
    """Creates a dot file"""
    wfile = pu.find_default_wfile(wfile)

    with open(wfile, 'r') as fp:
        wf = hcl.load(fp)

    name = list(wf["workflow"].keys())[0]

    action = wf["workflow"][name]["resolves"]
    parent_action = cur_action = action

    if not isinstance(cur_action, str):
        cur_action = cur_action[0]

    graph = list()
    graph = add(parent_action, cur_action, wf["action"], graph)
    graph = ''.join(list(set(graph)))
    graph = "digraph G {\n" + graph + "}\n"
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
    if cur_action != parent_action:
        graph.append("\t{} -> {};\n".format(
            parent_action.replace(' ', '_').replace('-', '_'),
            cur_action.replace(' ', '_').replace('-', '_')))

    return graph
