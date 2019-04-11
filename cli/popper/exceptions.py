import click
from click._compat import get_text_stderr
from click import secho
from click.exceptions import ClickException


class UsageError(ClickException):
    """An internal exception that signals a usage error and gives a
    colorized output.This typically aborts any further handling.

    :param message: the error message to display.
    :param ctx: optionally the context that caused this error.  Click will
            fill in the context automatically in some situations.
    """

    exit_code = 2

    def __init__(self, message, ctx=None):
        ClickException.__init__(self, message)
        self.ctx = ctx
        self.cmd = self.ctx and self.ctx.command or None

    def show(self, file=None, **styles):
        if file is None:
            file = get_text_stderr()

        if (self.cmd is not None and
                self.cmd.get_help_option(self.ctx) is not None):
            hint = ('Try "%s %s" for help. \n'
                    % (self.ctx.command_path, self.ctx.help_option_names[0]))

        secho(
            'Error: %s' %
            self.format_message(),
            file=file,
            fg='red',
            bold=True)


class BadArgumentUsage(UsageError):
    """ Raised if an argument is generally supplied but the use of the argument
    was incorrect.
    """

    def __init__(self, message, ctx=None):
        UsageError.__init__(self, message, ctx)
