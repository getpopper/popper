import click

from popper import utils as pu
from popper.cli import pass_context, log
from popper.gha import Workflow


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
@click.command('dot', short_help='Generate a graph in the .dot format.')
@pass_context
def cli(ctx, wfile, recursive):
    """
    Creates a graph in the .dot format representing the workflow.
    """
    def add_to_graph(graph_str, wf, parent, children):
        """Recursively goes through "next" and adds corresponding actions
        """
        _parent = parent.replace(' ', '_').replace('-', '_')
        for n in children:
            _n = n.replace(' ', '_').replace('-', '_')
            graph_str += "  {} -> {};\n".format(_parent, _n)
            for M in wf['action'][n].get('next', []):
                graph_str = add_to_graph(graph_str, wf, n, [M])

        return graph_str

    wfile_list = list()

    if recursive:
        wfile_list = pu.find_recursive_wfile()
    else:
        wfile_list.append(pu.find_default_wfile(wfile))

    for wfile in wfile_list:
        pipeline = Workflow(wfile, False, False, False, False, True)
        wf = pipeline.wf
        workflow_name = wf['name'].replace(' ', '_').replace('-', '_')
        graph_str = add_to_graph("", wf, workflow_name, wf['root'])
        log.info("digraph G {\n" + graph_str + "}\n")
