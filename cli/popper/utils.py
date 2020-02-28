import importlib.util
import os
import re
import threading
import yaml

from builtins import str
from distutils.spawn import find_executable
from dotmap import DotMap

from popper.cli import log


def setup_base_cache():
    """Set up the base cache directory.

    Args:
      None

    Returns:
      str: The path to the base cache directory.
    """
    if os.environ.get('POPPER_CACHE_DIR', None):
        base_cache = os.environ['POPPER_CACHE_DIR']
    else:
        cache_dir = os.environ.get('XDG_CACHE_HOME',
                                   os.path.join(os.environ['HOME'], '.cache'))
        base_cache = os.path.join(cache_dir, 'popper')

    os.makedirs(base_cache, exist_ok=True)

    return base_cache


def decode(line):
    """Make treatment of stdout Python 2/3 compatible.

    Args:
      line(str): The string that is required to be converted.

    Returns:
      str : The string in converted form.
    """
    if isinstance(line, bytes):
        return line.decode('utf-8')
    return line


class threadsafe_iter_3:
    """Takes an iterator/generator and makes it thread-safe by serializing call
    to the `next` method of given iterator/generator."""

    def __init__(self, it):
        self.it = it
        self.lock = threading.Lock()

    def __iter__(self):
        return self

    def __next__(self):
        with self.lock:
            return self.it.__next__()


def threadsafe_generator(f):
    """A decorator that takes a generator function and makes it thread-safe.

    Args:
      f(function): Generator function

    Returns:
      None
    """
    def g(*args, **kwargs):
        """

        Args:
          *args(list): List of non-key worded,variable length arguments.
          **kwargs(dict): List of key-worded,variable length arguments.

        Returns:
          function: The thread-safe function.
        """
        return threadsafe_iter_3(f(*args, **kwargs))
    return g


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


def write_file(path, content=''):
    """Create and write contents to a file. If no content is provided a blank
    file is created.

    Args:
      path(str): The path where the file would be created.
      content(str, optional): The content to write in the file.
                            (Default value = '')

    Returns:
      None
    """
    f = open(path, 'w')
    f.write(content)
    f.close()


def module_from_file(module_name, file_path):
    """Import a file as a module.

    Args:
      module_name(str): The name of the module.
      file_path(str): The path to the file to be imported.

    Returns:
      module
    """
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_config_file(config_file):
    """Validate and parse the engine configuration file.

    Args:
      config_file(str): Path to the file to be parsed.

    Returns:
      dict: Engine configuration.
    """
    if not os.path.exists(config_file):
        log.fail(f'File {config_file} was not found.')

    if not config_file.endswith('.py'):
        log.fail('Configuration file must be a python source file.')

    module_name = os.path.basename(config_file)[:-3]
    module = module_from_file(module_name, config_file)

    return module


def assert_executable_exists(command):
    """Check if the given command can be invoked; fails if not."""
    if not find_executable(command):
        log.fail(f"Could not find '{command}'.")


def prettystr(a):
    if type(a) == DotMap:
        a = a.toDict()
    if type(a) == os._Environ:
        a = dict(a)
    if type(a) == dict:
        return f'{yaml.dump(a, default_flow_style=False)}'
