import logging
import sys
import os

STEP_INFO = 15
logging.addLevelName(STEP_INFO, "STEP_INFO")

msg_prefix = ""


class PopperFormatter(logging.Formatter):
    """A Formatter which sets the format for popper custom log messages.

    Level Values are
    DEBUG: 10
    STEP_INFO: 15
    INFO: 20
    WARNING: 30
    ERROR: 40
    CRITICAL: 50

    The level STEP_INFO is used to log information produced solely by
    steps during popper execution.
    The popper default log level is STEP_INFO. On the usage of --quiet flag,
    we change the level to INFO, thus effectively silencing STEP_INFO log.

    In order of Level. The format of the logs is given in log_format dict.
    The log colors used are based on ANSI Escape Codes
    """

    # Log Colors
    BOLD_CYAN = "[01;36m"
    RESET = "[0m"
    BOLD_YELLOW = "[01;33m"
    BOLD_RED = "[01;31m"

    log_format = {
        "DEBUG": f"{BOLD_CYAN}%(levelname)s: %(msg)s {RESET}",
        "STEP_INFO": "%(msg)s",
        "INFO": "%(msg)s",
        "WARNING": f"{BOLD_YELLOW}%(levelname)s: %(msg)s{RESET}",
        "ERROR": f"{BOLD_RED}%(levelname)s: %(msg)s{RESET}",
        "CRITICAL": f"{BOLD_RED}%(levelname)s: %(msg)s{RESET}",
    }

    log_format_no_colors = {
        "DEBUG": "%(levelname)s: %(msg)s ",
        "STEP_INFO": "%(msg)s",
        "INFO": "%(msg)s",
        "WARNING": "%(levelname)s: %(msg)s",
        "ERROR": "%(levelname)s: %(msg)s",
        "CRITICAL": "%(levelname)s: %(msg)s",
    }

    def __init__(self, colors=True):
        super(PopperFormatter, self).__init__(fmt="%(levelname)s: %(msg)s")
        self.log_fmt = self.log_format if colors else self.log_format_no_colors

    def format(self, record):
        """

        Args:
          record(logging.LogRecord): The part of the log record from which
                                        the information is to be extracted.

        Returns:
          str: String containing meaningful information from logs.

        """
        fmt = self.log_fmt[logging.getLevelName(record.levelno)]
        if sys.version_info[0] < 3:
            self._fmt = fmt
        else:
            self._style._fmt = fmt
        result = f"{msg_prefix}{logging.Formatter.format(self, record)}"
        return result


class PopperLogger(logging.Logger):
    """A Logger so that we can add popper fail and step_info log methods."""

    def fail(self, msg="", *args, **kwargs):
        """Log a message with severity 'ERROR', and then exits.

        Args:
          msg(str, optional): Message to be logged.(Default value = '')
          *args(list): List of non-key worded,variable length arguments.
          **kwargs(dict): List of key-worded,variable length arguments.

        Returns:
          None
        """
        super(PopperLogger, self).error(msg, *args, **kwargs)
        sys.exit(1)

    def step_info(self, msg="", *args, **kwargs):
        """Log a message with severity 'STEP_INFO'.

        Args:
          msg(str, optional): Message to be logged.(Default value = '')
          *args(list): List of non-key worded,variable length arguments.
          **kwargs(dict): List of key-worded,variable length arguments.

        Returns:
          None
        """
        if self.isEnabledFor(STEP_INFO):
            self._log(STEP_INFO, msg, args, **kwargs)

    def error(self, msg, *args, **kwargs):
        """Sends a warning about the use of fail(). We are depreciating it in
        favor of fail()

        The error() method has been replaced with fail(), as fail is more
        indicative of the functionality provided i.e. fail() will also
        result in the failure of the module when called and stop execution.

        Args:
          msg(str, optional): Message to be logged.
          *args(list): List of non-key worded,variable length arguments.
          **kwargs(dict): List of key-worded,variable length arguments.

        Returns:
          None
        """
        super(PopperLogger, self).warning("error() has been replaced with fail()")
        pass

    def info(self, msg="", *args, **kwargs):
        """Logs a message with severity 'INFO'.

        Args:
          msg(str, optional): Message to be logged.(Default value = '')
          *args(list): List of non-key worded,variable length arguments.
          **kwargs(dict): List of key-worded,variable length arguments.

        Returns:
          None
        """
        super(PopperLogger, self).info(msg, *args, **kwargs)

    def debug(self, msg="", *args, **kwargs):
        """Logs a message with severity 'DEBUG'.

        Args:
          msg(str,optional): Message to be logged.(Default value = '')
          *args(list): List of non-key worded,variable length arguments.
          **kwargs(dict): List of key-worded,variable length arguments.

        Returns:
          None
        """
        super(PopperLogger, self).debug(msg, *args, **kwargs)

    def warning(self, msg="", *args, **kwargs):
        """Logs a message with severity 'WARNING'.

        Args:
          msg(str, optional): Message to be logged.(Default value = '')
          *args(list): List of non-key worded,variable length arguments.
          **kwargs(dict): List of key-worded,variable length arguments.

        Returns:
          None
        """
        super(PopperLogger, self).warning(msg, *args, **kwargs)


class LevelFilter(logging.Filter):
    """Filters the level that are to be accepted and rejected."""

    def __init__(self, passlevels, reject):
        self.passlevels = passlevels
        self.reject = reject

    def filter(self, record):
        """Returns True and False according to the pass levels and reject value.

        Args:
          record(logging.LogRecord): Record from logs.

        Returns:
          bool : True/False according to values of pass levels and level number
                of the record.
        """
        if self.reject:
            return record.levelno not in self.passlevels
        else:
            return record.levelno in self.passlevels


def setup_logging(level="STEP_INFO"):
    """Setups logging facilities with custom Logger and Formatter.

    Args:
      level(str): Level to be logged in custom logger.
                    (Default value = 'STEP_INFO')

    Returns:
      popper.log.PopperLogger: Custom log for that particular level.
    """
    logging.setLoggerClass(PopperLogger)
    log = logging.getLogger("popper")

    formatter = PopperFormatter()

    # INFO/STEP_INFO goes to stdout
    h1 = logging.StreamHandler(sys.stdout)
    h1.addFilter(LevelFilter([logging.INFO, STEP_INFO], False))
    h1.setFormatter(formatter)

    # anything goes to stdout
    h2 = logging.StreamHandler(sys.stderr)
    h2.addFilter(LevelFilter([logging.INFO, STEP_INFO], True))
    h2.setFormatter(formatter)

    log.addHandler(h1)
    log.addHandler(h2)
    log.setLevel(level)

    return log


def add_log(log, logfile):
    """It sets the formatter for the handle and add that handler to the logger.

    Args:
      log(Logging.logger): The logger object used for logging.
      logfile(str): path for the log file.

    Returns:
      None
    """
    dir = os.path.dirname(logfile)
    if not os.path.exists(dir) and dir != "":
        os.makedirs(dir)
    handler = logging.FileHandler(logfile)
    formatter = PopperFormatter(colors=False)

    # Set
    handler.setFormatter(formatter)
    log.addHandler(handler)
