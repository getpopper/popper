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
@click.option(
    '--recursive',
    help='Generate .dot file for any.workflow file '
         'found recursively from current path.',
    required=False,
    is_flag=True
)
@click.command('dot', short_help='Generates a .dot format for a given workflow'
               '\n[.dot is a format for graphical representation]')
@pass_context
def cli(ctx, wfile, recursive):
    """
    Analyzes a workflow file and then creates a dot representation for the same
    .dot represents the order in which actions in the workflow must be executed
    """
    wfile_list = list()
    if recursive:
        wfile_list = pu.find_recursive_wfile()
    else:
        wfile_list.append(pu.find_default_wfile(wfile))

    for wfile in wfile_list:
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
