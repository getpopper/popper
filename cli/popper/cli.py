import difflib
import os
import signal
import sys

import click
from click.exceptions import ClickException

import popper.log as logging

from popper import __version__

log = logging.setup_logging()
popper_version = __version__
cmd_folder = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                          'commands'))


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
            if filename.endswith('.py') and filename.startswith('cmd_'):
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
        try:
            if sys.version_info[0] == 2:
                name = name.encode('ascii', 'replace')
            mod = __import__('popper.commands.cmd_' + name,
                             None, None, ['cli'])
        except ImportError as e:
            commands = self.list_commands(ctx)
            most_similar_commands = ", ".join(
                difflib.get_close_matches(
                    name, commands, 3, 0.3))
            message = ""
            if len(most_similar_commands) != 0:
                message = "\n\nThe most similar commands are: " \
                    + most_similar_commands
            raise ClickException(
                "Command '" + name + "' doesn't exist.\n"
                "Type 'popper --help' for more.\n" + message + '\n' + str(e)
            )
        return mod.cli


@click.command(cls=PopperCLI)
@pass_context
def cli(ctx):
    """Popper command line interface."""
    from popper.runner import WorkflowRunner
    signal.signal(signal.SIGINT, WorkflowRunner.signal_handler)
    signal.signal(signal.SIGUSR1, WorkflowRunner.signal_handler)
