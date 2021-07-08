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
    "infmt",
    "--from",
    help="Format of the input file.",
    type=click.Choice(["popper"]),
    default="popper",
)
@click.option(
    "infile",
    "--file",
    "-f",
    help="File containing the definition of the workflow.",
    required=False,
    default=".popper.yml",
)
@click.option(
    "outfmt",
    "--to",
    help="Format of the output file.",
    type=click.Choice(["drone"]),
    default="drone",
)
@click.option(
    "outfile", "--out", help="Name of the output file.", required=False,
)
@pass_context
def cli(ctx, infmt, infile, outfmt, outfile):
    if outfile is None:
        if outfmt == "drone":
            outfile = ".drone.yml"
    translator = WorkflowTranslator.get_translator(outfmt)
    wf = WorkflowParser.parse(file=infile)
    translated = translator.translate(wf)
    with open(outfile, "w") as f:
        f.write(translated)
    log.info(f"Translated to {outfmt} configuration successfully.")
