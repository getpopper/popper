import os
import signal
import sys
import time

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
    if interrupt_params.parallel:
        for future in flist:
            future.cancel()     # Try to safely exit threads

    # This will kill everything
    for pid in process_list:
        try:
            os.kill(pid, signal.SIGTERM)
        except OSError:
            # Process was probably already killed, so exit silently
            pass

    pu.info("\n")
    cmd_out = pu.exec_cmd('docker ps -a --format "{{.Names}}"')
    cmd_out = cmd_out[0].splitlines()
    cmd_out = set(cmd_out)

    for img in set(docker_list).intersection(cmd_out):
        pu.exec_cmd('docker stop {}'.format(img))
        if interrupt_params.reuse:
            pu.info('--reuse flag is set. Retaining containers')
            msg = '\nStopping {}'.format(img)
        else:
            msg = '\nDeleting {}'.format(img)
            pu.exec_cmd('docker rm -f {}'.format(img))
        pu.info(msg)
    pu.info('\n')


    sys.exit(0)
