import click
import os
import traceback

from popper.cli import pass_context, log
from popper.parser import WorkflowParser
from popper.translators.translator import WorkflowTranslator


@click.command(
    "translate",
    short_help="Translate workflow configuration files of different runners.",
)
@click.option(
    "from_fmt",
    "--from",
    help="Format of the input file.",
    type=click.Choice(["popper"]),
    default="popper",
)
@click.option(
    "file",
    "--file",
    "-f",
    help="File containing the definition of the workflow.",
    required=False,
    default=".popper.yml",
)
@click.option(
    "to_fmt",
    "--to",
    help="Format of the output file.",
    type=click.Choice(["drone"]),
    default="drone",
)
@pass_context
def cli(ctx, from_fmt, file, to_fmt):
    if to_fmt == "drone":
        outfile = ".drone.yml"
    translator = WorkflowTranslator.get_translator(to_fmt)
    wf = WorkflowParser.parse(file=file)
    try:
        translated = translator.translate(wf)
    except Exception as e:
        log.debug(traceback.format_exc())
        log.fail(e)
    with open(outfile, "w") as f:
        f.write(translated)
    log.info(f"Translated to {to_fmt} configuration successfully.")
