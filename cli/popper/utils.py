import os
import re
import threading
import yaml

from builtins import str
from distutils.spawn import find_executable
from subprocess import Popen, STDOUT, PIPE, SubprocessError

from popper.cli import log


def sanitized_name(name, wid=''):
    """Clean a step name and change it to proper format. It replaces all the
    unwanted characters with `_`.

    Args:
      name(str): The crud step name.
      wid(str): It  is a workflow ID produced by a utils.get_id().

    Returns:
      str: The sanitize step name.
    """
    return f"popper_{re.sub('[^a-zA-Z0-9_.-]', '_', name)}_{wid}"


def of_type(param, valid_types):
    """Function to check the type of a parameter.

    It tries to match the type of the parameter with the
    types passed through `valid_types` list.

    Args:
      param: A value of any type.
      valid_types(list): A list of acceptable types.

    Returns:
      bool: True/False, depending upon whether the type of
      the passed param matches with any of the valid types.
    """
    for t in valid_types:
        if t == 'str':
            if isinstance(param, str):
                return True

        if t == 'dict':
            if isinstance(param, dict):
                return True

        if t == 'los':
            if isinstance(param, list):
                res = list(map(lambda a: isinstance(a, str), param))
                return False not in res

    return False


def assert_executable_exists(command):
    """Check if the given command can be invoked; fails if not."""
    if not find_executable(command):
        log.fail(f"Could not find '{command}'.")


def prettystr(a):
    if isinstance(a, os._Environ):
        a = dict(a)
    if isinstance(a, dict):
        return f'{yaml.dump(a, default_flow_style=False)}'


def exec_cmd(cmd, env=None, cwd=os.getcwd(), pids=set(), logging=True):
    pid = 0
    try:
        with Popen(cmd, stdout=PIPE, stderr=STDOUT,
                   universal_newlines=True, preexec_fn=os.setsid,
                   env=env, cwd=cwd) as p:
            pid = p.pid
            pids.add(p.pid)
            log.debug('Reading process output')

            output = ""
            for line in iter(p.stdout.readline, ''):
                line_decoded = decode(line)
                if logging:
                    log.step_info(line_decoded[:-1])
                else:
                    output += line_decoded

            p.wait()
            ecode = p.poll()

        log.debug(f'Code returned by process: {ecode}')

    except SubprocessError as ex:
        output = ""
        ecode = ex.returncode
        log.step_info(f"Command '{cmd[0]}' failed with: {ex}")
    except Exception as ex:
        output = ""
        ecode = 1
        log.step_info(f"Command raised non-SubprocessError error: {ex}")

    return pid, ecode, output


def select_not_none(array):
    for item in array:
        if item:
            return item
