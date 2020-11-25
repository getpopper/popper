import click
import os

from popper.cli import pass_context, log
from popper.exporter import WorkflowExporter


@click.command("ci", short_help="Generate CI service configuration files.")
@click.argument(
    "service", type=click.Choice(["travis"]), required=True,
)
@click.option(
    "-f",
    "--file",
    help="Workflow file to be executed by CI service job.",
    required=False,
    default=".popper.yml",
)
@click.option(
    "-s",
    "--substitution",
    help="A key-value pair defining a substitution. Can be given multiple times.",
    required=False,
    default=list(),
    multiple=True,
)
@pass_context
def cli(ctx, service, file, substitution):
    """Generates configuration files for distinct CI services. This command
    needs to be executed on the root of your Git repository folder.
    """
    if not os.path.exists(".git"):
        log.fail(
            "This command needs to be executed on the root of your "
            "Git project folder (where the .git/ folder is located)."
        )
    exporter = WorkflowExporter.get_exporter(service)
    exporter.export(file, substitution)
    log.info(f"Wrote {service} configuration successfully.")
