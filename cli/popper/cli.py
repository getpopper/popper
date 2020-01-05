import difflib
import os
import signal
import sys

import click
from click.exceptions import ClickException

from popper import __version__ as popper_version, log as log


class Context(object):
    """Context Class.For more details refer
    https://click.palletsprojects.com/en/7.x/commands/#custom-multi-commands .
    """
    pass


log = log.setup_logging()
pass_context = click.make_pass_decorator(Context, ensure=True)
cmd_folder = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                          'commands'))
popper_version = popper_version


class PopperCLI(click.MultiCommand):
    """Provides CLI interface for Popper."""

    def list_commands(self, ctx):
        """Returns the list of available commands in sorted order.

        Args:
            ctx(popper.cli.context):For process intercommand communication
            context is used.For reference visit
            https://click.palletsprojects.com/en/7.x/commands/#nested-handling-and-contexts .

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
          ctx(popper.cli.context):ctx(popper.cli.context):For process intercommand communication
            context is used.For reference visit
            https://click.palletsprojects.com/en/7.x/commands/#nested-handling-and-contexts .
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
                "Command '" + name + "' doesn't exist. " +
                "\nType 'popper --help' for more."
                + message + '\n' + str(e)
            )
        return mod.cli


@click.command(cls=PopperCLI)
@pass_context
def cli(ctx):
    """Popper command line interface.

    Args:
      ctx(popper.cli.context):ctx(popper.cli.context):For process intercommand communication
            context is used.For reference visit
            https://click.palletsprojects.com/en/7.x/commands/#nested-handling-and-contexts .

    Returns:
        None
    """
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGUSR1, signal_handler)


docker_list = list()
vagrant_list = list()
process_list = list()
interrupt_params = dict()
flist = None


def signal_handler(sig, frame):
    """Handles the interrupt signal.

    Args:
        sig(int): Signal number of signal being passed to cli.
        frame(class):It represents execution frame. For more
            details visit
            https://docs.python.org/3/reference/datamodel.html#frame-objects .

    Returns:
        None
    """
    if interrupt_params.get('parallel', None) and flist:
        for future in flist:
            future.cancel()

    for pid in process_list:
        log.info("Stopping process '{}'".format(pid))
        try:
            os.killpg(os.getpgid(pid), signal.SIGTERM)
        except OSError:
            pass

    for container in docker_list:
        log.info("Stopping container '{}'".format(container.name))
        container.stop(timeout=1)

    if vagrant_list:
        import vagrant
        for box_path in vagrant_list:
            log.info("Stopping box '{}'".format(box_path))
            vagrant.Vagrant(root=box_path).halt()

    sys.exit(0)
