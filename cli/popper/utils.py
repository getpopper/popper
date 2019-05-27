import os
import sys
import threading

from popper.cli import log


def decode(line):
    """Make treatment of stdout Python 2/3 compatible"""
    if isinstance(line, bytes):
        return line.decode('utf-8')
    return line


def get_items(dict_object):
    """Python 2/3 compatible way of iterating over a dictionary"""
    for key in dict_object:
        yield key, dict_object[key]


class threadsafe_iter_3:
    """Takes an iterator/generator and makes it thread-safe by
    serializing call to the `next` method of given iterator/generator.
    """

    def __init__(self, it):
        self.it = it
        self.lock = threading.Lock()

    def __iter__(self):
        return self

    def __next__(self):
        with self.lock:
            return self.it.__next__()


class threadsafe_iter_2:
    """Takes an iterator/generator and makes it thread-safe by
    serializing call to the `next` method of given iterator/generator.
    """

    def __init__(self, it):
        self.it = it
        self.lock = threading.Lock()

    def __iter__(self):
        return self

    def next(self):
        with self.lock:
            return self.it.next()


def threadsafe_generator(f):
    """A decorator that takes a generator function and makes it thread-safe.
    """
    def g(*args, **kwargs):
        if sys.version_info[0] < 3:
            return threadsafe_iter_2(f(*args, **kwargs))
        else:
            return threadsafe_iter_3(f(*args, **kwargs))
    return g


def find_default_wfile(wfile):
    """
    Used to find `main.workflow` in $PWD or in `.github`
    And returns error if not found

    Returns:
        path of wfile
    """
    if not wfile:
        if os.path.isfile("main.workflow"):
            wfile = "main.workflow"
        elif os.path.isfile(".github/main.workflow"):
            wfile = ".github/main.workflow"

    if not wfile:
        log.fail(
            "Files {} or {} not found.".format("./main.workflow",
                                               ".github/main.workflow"))
    if not os.path.isfile(wfile):
        log.fail("File {} not found.".format(wfile))
        exit(1)

    return wfile


def find_recursive_wfile():
    """
    Used to search for `.workflow` files in $PWD and
    then recursively in sub directories

    Returns:
        list of path of workflow files
    """
    wfile_list = list()
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.workflow'):
                wfile = os.path.join(root, file)
                wfile = os.path.abspath(wfile)
                wfile_list.append(wfile)
    return wfile_list
