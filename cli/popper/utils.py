import os
import re
import hashlib
import threading
import importlib.util
from builtins import str

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
        base_cache = os.path.join(
            os.environ.get(
                'XDG_CACHE_HOME',
                os.path.join(
                    os.environ['HOME'],
                    '.cache')),
            'popper')

    if not os.path.exists(base_cache):
        os.makedirs(base_cache)

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


def find_recursive_wfile():
    """Used to search for `.workflow` files in $PWD and then recursively in sub
    directories.

    Args:
      None

    Returns:
      list: List of path of workflow files.
    """
    wfile_list = list()
    for root, _, files in os.walk('.'):
        for file in files:
            if file.endswith('.workflow'):
                wfile = os.path.join(root, file)
                wfile = os.path.abspath(wfile)
                wfile_list.append(wfile)
    return wfile_list


def sanitized_name(name, wid):
    """Clean an action name and change it to proper format. It replaces all the
    unwanted characters with `_`.

    Args:
      name(str): The crude action name.
      wid(str): It  is a workflow ID produced by a utils.get_id().

    Returns:
      str: The sanitized action name.
    """
    return "popper_{}_{}".format(
        re.sub('[^a-zA-Z0-9_.-]', '_', name),
        wid
    )


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


def get_id(*args):
    """Function to generate an unique hashid for identifying a workflow by
    joining the args provided.

    Args:
      args(tuple): The items to join in order to form
    an identifier.

    Returns:
      str: The generated hashid.
    """
    identifier = '_'.join([str(x) for x in args])
    workflow_id = str(hashlib.md5(identifier.encode()).hexdigest())
    return workflow_id


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


def parse_engine_configuration(engine_conf_file):
    """Validate and parse the engine configuration file.

    Args:
      engine_conf_file(str): Path to the file to be parsed.

    Returns:
      dict: Engine configuration.
    """
    if not engine_conf_file:
        return None

    if not os.path.exists(engine_conf_file):
        log.fail('File {} was not found.'.format(engine_conf_file))

    if not engine_conf_file.endswith('.py'):
        log.fail('Config file must be a python source file.')

    module_name = os.path.basename(engine_conf_file)[:-3]
    module = module_from_file(module_name, engine_conf_file)

    try:
        return module.engine_configuration
    except AttributeError:
        log.fail('No variable named \"engine_configuration\" was found.')
