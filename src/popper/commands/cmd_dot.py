import click

from popper.cli import pass_context, log
from popper.parser import WorkflowParser


@click.option(
    "-f",
    "--file",
    help="File containing the definition of the workflow.",
    required=True,
)
@click.option(
    "--skip",
    help=("Skip the list of steps specified."),
    required=False,
    default=list(),
    multiple=True,
)
@click.option(
    "--colors", help="Use colors in the graph.", required=False, is_flag=True,
)
@click.command("dot", short_help="Generate a graph in the .dot format.")
@pass_context
def cli(ctx, file, skip, colors):
    """Creates a graph in the .dot format representing the workflow."""
    wf = WorkflowParser.parse(file=file)

    node_attrs = 'shape=box, style="filled{}", fillcolor=transparent{}'
    wf_attr = node_attrs.format(",rounded", ",color=red" if colors else "")
    act_attr = node_attrs.format("", ",color=cyan" if colors else "")
    dot_str = ""
    dot_str += f'  "Workflow" [{wf_attr}];\n'
    for i, step in enumerate(wf.steps):
        n = wf.steps[i]["id"]
        dot_str += f'  "{n}" [{act_attr}];\n'
        if i == 0:
            parent = "Workflow"
        else:
            parent = wf.steps[i - 1]["id"]
        dot_str += f'  "{parent}" -> "{n}";\n'
    log.info("digraph G { graph [bgcolor=transparent];\n" + dot_str + "}\n")
