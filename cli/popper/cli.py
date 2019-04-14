import os
import signal
import sys
import click
import difflib
from . import __version__ as popper_version
from .exceptions import UsageError
import popper.utils as pu


class Context(object):

    def __init__(self):
        self.verbose = False
        self.home = os.getcwd()

    def log(self, msg, *args):
        """Logs a message to stderr."""
        if args:
            msg %= args
        click.echo(msg, file=sys.stderr)

    def vlog(self, msg, *args):
        """Logs a message to stderr only if verbose is enabled."""
        if self.verbose:
            self.log(msg, *args)


pass_context = click.make_pass_decorator(Context, ensure=True)
cmd_folder = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                          'commands'))
popper_version = popper_version


class PopperCLI(click.MultiCommand):

    def list_commands(self, ctx):
        rv = []
        for filename in os.listdir(cmd_folder):
            if filename.endswith('.py') and filename.startswith('cmd_'):
                rv.append(filename[4:-3])
        rv.sort()
        return rv

    def get_command(self, ctx, name):
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
            raise UsageError(
                "Command '" + name + "' doesn't exist. " +
                "\nType 'popper --help' for more."
                + message + '\n' + str(e)
            )
        return mod.cli


@click.command(cls=PopperCLI)
@pass_context
def cli(ctx):
    """Popper command line interface."""
    signal.signal(signal.SIGINT, signal_handler)


docker_list = list()
process_list = list()
interrupt_params = None
flist = None

def signal_handler(sig, frame):

    pu.info('Caught Ctrl-C signal! Stopping running actions.\n')

    if interrupt_params.parallel:
        for future in flist:
            future.cancel()

    for pid in process_list:
        pu.info("Stopping process '{}'\n".format(pid))
        try:
            os.killpg(os.getpgid(pid), signal.SIGTERM)
        except OSError:
            pass

    for container in docker_list:
        pu.info("Stopping container '{}'\n".format(container.name))
        pu.exec_cmd('docker stop -t 1 {}'.format(container.name))

    sys.exit(0)
