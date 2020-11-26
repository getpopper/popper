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
    """Display help for a given command or popper default help"""
    if subcommand:
        target_command = popper_cli.get_command(ctx, subcommand)
        log.info(target_command.get_help(click.Context(popper_cli)))
        # log.info("")      # popper is not happy with this line
    else:
        log.info(popper_cli.get_help(click.Context(popper_cli)))

        log.info("")
        log.info(
            """If you enjoy using popper, please leave us a star
                 at https://github.com/getpopper/popper!"""
        )
        log.info("")
        log.info(
            """If you have encountered any bugs or issues, please start a
                 discussion at the github repository"""
        )
        log.info("or discuss Popper with us in our slack at the following link:")
        log.info("https://bit.ly/join-popper-slack")
        log.info("")
        log.info(
            """Finally, please give us your feedback using this survey!
            https://bit.ly/popper-survey"""
        )
