import difflib
import importlib
import os
import signal

import click

import popper.log as logging

from popper import __version__

log = logging.setup_logging()
popper_version = __version__
cmd_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "commands"))


class Context(object):
    """Context Class.For more details refer
    https://click.palletsprojects.com/en/7.x/commands/#custom-multi-commands .
    """

    pass


pass_context = click.make_pass_decorator(Context, ensure=True)


class PopperCLI(click.MultiCommand):
    """Provides CLI interface for Popper."""

    def list_commands(self, ctx):
        """Returns the list of available commands in sorted order.

        Args:
          ctx(popper.cli.context): For process inter-command communication.
          For reference visit https://click.palletsprojects.com/en/7.x

        Returns:
          list: Returns the list of available commands.
        """
        rv = []
        for filename in os.listdir(cmd_folder):
            if filename.endswith(".py") and filename.startswith("cmd_"):
                rv.append(filename[4:-3])
        rv.sort()
        return rv

    def get_command(self, ctx, name):
        """Imports the command if available in commmands list and provides with
        most similar commands if the command is not present in the list.

        Args:
          name(str): The name of the command.

        Returns:
          click.core.Command: It is a new command and uses the decorated
            function as callback.For reference visit
            https://click.palletsprojects.com/en/7.x/api/#decorators .
        """
        cmd_path = f"popper.commands.cmd_{name}"
        cmd_spec = importlib.util.find_spec(cmd_path)

        if cmd_spec is not None:
            # found it
            cmd_mod = importlib.import_module(cmd_path)
            return cmd_mod.cli

        # given command doesn't exist, find a similarly named one
        commands = self.list_commands(ctx)
        similar_cmd = ", ".join(difflib.get_close_matches(name, commands, 1, 0.3))
        log.fail(
            f"Command '{name}' doesn't exist, did you mean '{similar_cmd}'? "
            "Run 'popper help' for more."
        )


@click.command(cls=PopperCLI)
@click.version_option(__version__, message=f"Popper version {popper_version}")
@pass_context
def cli(ctx):
    """Popper command line interface."""
    from popper.runner import WorkflowRunner

    signal.signal(signal.SIGINT, WorkflowRunner.signal_handler)
    signal.signal(signal.SIGUSR1, WorkflowRunner.signal_handler)
