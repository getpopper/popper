import click
import os

from popper.cli import pass_context, log
from popper.parser import WorkflowParser
from popper.translators.translater import WorkflowTranslator


@click.command(
    "translate",
    short_help="Translate workflow configuration files of different runners.",
)
@click.option(
    "--file",
    "-f",
    help="File containing the definition of the workflow.",
    required=False,
    default=".popper.yml",
)
@click.option(
    "fmt",
    "--format",
    help="Format of the output file.",
    type=click.Choice(["drone"]),
    default="drone",
)
@click.option(
    "outfile",
    "--out",
    help="Name of the output file.",
    required=False,
)
@pass_context
def cli(ctx, file, fmt, outfile):
    if outfile is None:
        if fmt == "drone":
            outfile = ".drone.yml"
    translator = WorkflowTranslator.get_translator(fmt)
    wf = WorkflowParser.parse(file=file)
    translated = translator.translate(wf)
    with open(outfile, "w") as f:
        f.write(translated)
    log.info(f"Translated to {fmt} configuration successfully.")
