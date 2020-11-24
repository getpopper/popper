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

    #User can opt out of getting this message (change this check!)
    if True:
        log.info("")
        log.info("If you enjoy using popper, please leave us a star at https://github.com/getpopper/popper!")
        log.info("")
        log.info("If you have encountered any bugs or issues, please start a discussion at the github repository")
        log.info("or discuss Popper with us in our slack at the following link:")
        log.info("https://join.slack.com/t/getpopper/shared_invite/zt-dtn0se2s-c50myMHNpeoikQXDeNbPew.")
        log.info("")
        log.info("Finally, please give us your feedback using this survey! https://forms.gle/h1geK98fDboEhMXL6")
        #log.info("")
        #log.info("If you don't want to see this message in the future,")
        #userInput = input("please type \"stop\".")
        #if (userInput == "stop")
            # this is incomplete. Need to write to config file
            # Consider creating a "survey" file.
            #self._config.survey = False

