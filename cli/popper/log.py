import logging
import sys
import os
import datetime

ACTION_INFO = 15
logging.addLevelName(ACTION_INFO, 'ACTION_INFO')


class PopperFormatter(logging.Formatter):
    """
    A Formatter which sets the format for popper custom log messages

    Level Values are
    DEBUG: 10
    ACTION_INFO: 15
    INFO: 20
    WARNING: 30
    ERROR: 40
    CRITICAL: 50

    The level ACTION_INFO is used to log information produced solely by
    actions during popper execution.
    The popper default log level is ACTION_INFO. On the usage of --quiet flag,
    we change the level to INFO, thus effectively silencing ACTION_INFO log.

    In order of Level. The format of the logs is given in log_format dict.
    The log colors used are based on ANSI Escape Codes
    """
    # Log Colors
    BOLD_CYAN = '[01;36m'
    RESET = '[0m'
    BOLD_YELLOW = '[01;33m'
    BOLD_RED = '[01;31m'

    log_format = {
        'DEBUG':       '{}%(levelname)s: %(msg)s {}'.format(BOLD_CYAN, RESET),
        'ACTION_INFO': '%(msg)s',
        'INFO':        '%(msg)s',
        'WARNING':     '{}%(levelname)s: %(msg)s{}'.format(BOLD_YELLOW, RESET),
        'ERROR':       '{}%(levelname)s: %(msg)s{}'.format(BOLD_RED, RESET),
        'CRITICAL':    '{}%(levelname)s: %(msg)s{}'.format(BOLD_RED, RESET)
    }

    log_format_no_colors = {
        'DEBUG': '%(levelname)s: %(msg)s ',
        'ACTION_INFO': '%(msg)s',
        'INFO': '%(msg)s',
        'WARNING': '%(levelname)s: %(msg)s',
        'ERROR': '%(levelname)s: %(msg)s',
        'CRITICAL': '%(levelname)s: %(msg)s'
    }

    def __init__(self, colors=True):
        super(PopperFormatter, self).__init__(fmt='%(levelname)s: %(msg)s')
        self.log_fmt = self.log_format if colors else self.log_format_no_colors

    def format(self, record):
        fmt = self.log_fmt[logging.getLevelName(record.levelno)]
        if sys.version_info[0] < 3:
            self._fmt = fmt
        else:
            self._style._fmt = fmt
        result = logging.Formatter.format(self, record)
        return result


class PopperLogger(logging.Logger):
    """
    A Logger so that we can add popper fail and action_info log methods
    """

    @staticmethod
    def remove(msg):
        return msg[:-1] if msg.endswith('\n') else msg

    def fail(self, msg='', *args, **kwargs):
        """
        Log a message with severity 'ERROR', and then exits.
        """
        msg = self.remove(msg)
        super(PopperLogger, self).error(msg, *args, **kwargs)
        sys.exit(1)

    def action_info(self, msg='', *args, **kwargs):
        """
        Log a message with severity 'ACTION_INFO'.
        """
        msg = self.remove(msg)
        if self.isEnabledFor(ACTION_INFO):
            self._log(ACTION_INFO, msg, args, **kwargs)

    def error(self, msg, *args, **kwargs):
        """
        Logs a message with severity 'ERROR', and then exits.

        The error() method has been replaced with fail(), as fail is more
        indicative of the functionality provided i.e. fail() will also
        result in the failure of the module when called
        """
        msg = self.remove(msg)
        super(PopperLogger, self).\
            warning('Note: error() has been replaced with fail()')
        pass

    def info(self, msg='', *args, **kwargs):
        """
        Logs a message with severity 'INFO'

        Wrapper so that we can use info() instead of info('')
        """
        msg = self.remove(msg)
        super(PopperLogger, self).info(msg, *args, **kwargs)

    def debug(self, msg='', *args, **kwargs):
        """
        Logs a message with severity 'DEBUG'

        Wrapper so that we can use debug() instead of debug('')
        """
        msg = self.remove(msg)
        super(PopperLogger, self).debug(msg, *args, **kwargs)

    def warning(self, msg='', *args, **kwargs):
        """
        Logs a message with severity 'WARNING'

        Wrapper so that we can use warning() instead of warning('')
        """
        msg = self.remove(msg)
        super(PopperLogger, self).warning(msg, *args, **kwargs)


def setup_logging(level='ACTION_INFO'):
    logging.setLoggerClass(PopperLogger)
    log = logging.getLogger('popper')
    formatter = PopperFormatter()
    handler = logging.StreamHandler(sys.stdout)

    # Set
    handler.setFormatter(formatter)
    log.addHandler(handler)
    log.setLevel(level)
    return log


def add_log(log, logfile):
    logfile = 'popper_logs/log' if logfile is None else logfile
    if logfile == 'popper_logs/log':
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        logfile += '_' + timestamp
    dir = os.path.dirname(logfile)
    if not os.path.exists(dir) and dir!='':
        os.makedirs(dir)
    handler = logging.FileHandler(logfile)
    formatter = PopperFormatter(colors=False)

    # Set
    handler.setFormatter(formatter)
    log.addHandler(handler)
