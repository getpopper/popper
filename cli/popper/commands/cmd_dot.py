import click

from popper import utils as pu
from popper.cli import pass_context, log
from popper.gha import WorkflowRunner


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
    def add_to_graph(graph_set, wf, parent, children):
        """Recursively goes through "next" and adds corresponding actions
        """
        _parent = parent.replace(' ', '_').replace('-', '_')
        for n in children:
            _n = n.replace(' ', '_').replace('-', '_')
            graph_set.add("  {} -> {};".format(_parent, _n))
            for M in wf.get_action(n).get('next', []):
                graph_set = add_to_graph(graph_set, wf, n, [M])

        return graph_set

    wfile_list = list()

    if recursive:
        wfile_list = pu.find_recursive_wfile()
    else:
        wfile_list.append(pu.find_default_wfile(wfile))

    for wfile in wfile_list:
        pipeline = WorkflowRunner(wfile, False, False, False, False, True)
        wf = pipeline.wf
        workflow_name = wf.name.replace(' ', '_').replace('-', '_')
        graph_set = add_to_graph(set(), wf, workflow_name, wf.root)
        graph_str = "\n".join(graph_set)
        workflow_attr = " [ shape=diamond, bordercolor=blue, border=bold]"
        digraph = "\n".join(
            [
                "digraph G {",
                workflow_name + workflow_attr,
                graph_str,
                "}"
            ]
        )
        log.info(digraph)
