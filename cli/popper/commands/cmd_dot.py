import click
from popper import utils as pu
from popper.cli import pass_context
from popper.gha import Workflow
from ..cli import log

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
@click.command('dot', short_help='Generate a graph in the .dot format')
@pass_context
def cli(ctx, wfile, recursive):
    """
    Creates a graph in the .dot format representing the workflow
    """
    wfile_list = list()
    if recursive:
        wfile_list = pu.find_recursive_wfile()
    else:
        wfile_list.append(pu.find_default_wfile(wfile))

    for wfile in wfile_list:
        pipeline = Workflow(wfile, False, False, False, False, False, False)

        graph = list()

        wf = pipeline.wf
        workflow_name = list(wf['workflow'].keys())[0]

        action = wf['resolves'][0]
        last_action = get_first_action(wf)

        for act in last_action:
            graph.append("\t{} -> {};\n".format(
                workflow_name.replace(' ', '_').replace('-', '_'),
                act.replace(' ', '_').replace('-', '_')))

        parent_action = cur_action = action
        graph = add(parent_action, cur_action, wf['action'], graph)
        graph = ''.join(list(set(graph)))
        graph = "digraph G {\n" + graph + "}\n"
        log.info(graph)


# Recursively go through "needs" and add corresponding actions to graph
def add(parent_action, cur_action, actions, graph):

    if 'needs' in actions[cur_action]:
        action_list = actions[cur_action]['needs']
        for act in action_list:
            graph = add(cur_action, act, actions, graph)

    # Adds edges to the graph
    if cur_action != parent_action:
        graph.append("\t{} -> {};\n".format(
            cur_action.replace(' ', '_').replace('-', '_'),
            parent_action.replace(' ', '_').replace('-', '_')))

    return graph


def get_first_action(wf):
    actions = list()
    for act in wf['action']:
        if act in wf['action']:
            if 'needs' not in wf['action'][act]:
                actions.append(act)
    return actions
