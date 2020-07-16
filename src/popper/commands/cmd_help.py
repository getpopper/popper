import click

from popper.cli import pass_context, log, PopperCLI

popper_cli = PopperCLI()


@click.command("help", short_help="Shows help for a given command.")
@click.argument(
    "subcommand",
    type=click.Choice(popper_cli.list_commands(click.Context(popper_cli))),
    required=False,
)
@pass_context
def cli(ctx, subcommand):
    """ Display help for a given command or popper default help
    """
    if subcommand:
        target_command = popper_cli.get_command(ctx, subcommand)
        log.info(target_command.get_help(click.Context(popper_cli)))
    else:
        log.info(popper_cli.get_help(click.Context(popper_cli)))
