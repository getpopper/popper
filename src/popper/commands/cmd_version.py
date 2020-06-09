import click

from popper import __version__ as popper_version
from popper.cli import pass_context, log


@click.command("version", short_help="Show version of Popper and exit.")
@pass_context
def cli(ctx):
    """Displays version of Popper and exit.
    """

    # Args:
    #   ctx(Popper.cli.context): For process inter-command communication
    #         context is used.For reference visit
    #         https://click.palletsprojects.com/en/7.x/commands/#nested-handling-and-contexts .

    # Returns:
    #   None

    log.info(f"Popper version {popper_version}")
