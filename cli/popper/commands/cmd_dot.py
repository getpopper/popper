import click

from popper import utils as pu
from popper.cli import pass_context, log
from popper.parser import Workflow


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
    '--skip',
    help=('Skip the list of actions specified.'),
    required=False,
    default=list(),
    multiple=True
)
@click.option(
    '--recursive',
    help='Generate .dot file for any.workflow file '
         'found recursively from current path.',
    required=False,
    is_flag=True
)
@click.option(
    '--colors',
    help='Use colors in the graph.',
    required=False,
    is_flag=True,
)
@click.command('dot', short_help='Generate a graph in the .dot format.')
@pass_context
def cli(ctx, wfile, skip, recursive, colors):
    """
    Creates a graph in the .dot format representing the workflow.
    """
    def add_to_graph(dot_str, wf, parent, children, node_attrs, stage_edges):
        """Recursively goes over the children ("next" attribute) of the given
        parent, adding an edge from parent to children
        """
        for n in children:
            edge = '  "{}" -> "{}";\n'.format(parent, n)
            if edge in stage_edges:
                continue
            dot_str += edge + '  "{}" [{}];\n'.format(n, node_attrs)

            stage_edges.add(edge)

            for M in wf.get_action(n).get('next', []):
                dot_str = add_to_graph(dot_str, wf, n, [M],
                                       node_attrs, stage_edges)
        return dot_str

    wfile_list = list()

    if recursive:
        wfile_list = pu.find_recursive_wfile()
    else:
        wfile_list.append(pu.find_default_wfile(wfile))

    for wfile in wfile_list:
        wf = Workflow(wfile)
        wf.skip_actions(skip)
        wf.check_for_unreachable_actions()

        node_attrs = (
            'shape=box, style="filled{}", fillcolor=transparent{}'
        )
        wf_attr = node_attrs.format(',rounded', ',color=red' if colors else '')
        act_attr = node_attrs.format('', ',color=cyan' if colors else '')
        dot_str = add_to_graph("", wf, wf.name, wf.root, act_attr, set())
        dot_str += '  "{}" [{}];\n'.format(wf.name, wf_attr)
        log.info(
            "digraph G { graph [bgcolor=transparent];\n" + dot_str + "}\n"
        )
