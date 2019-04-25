import os
import sys
import threading
import time
import popper.cli
from subprocess import CalledProcessError, PIPE, Popen, STDOUT
from popper.cli import log


def exec_cmd(cmd, ignore_error=False,
             dry_run=False, add_to_process_list=False):

    # If dry_run is True, I don't want the command to be executed
    # just an empty return

    if dry_run:
        return "", 0    # No error occurred

    # internal nested function to make treatment of stdout 2 and 3 compatible
    def b(t):
        if isinstance(t, bytes):
            return t.decode('utf-8')
        return t

    ecode = None

    sleep_time = 0.25
    num_times_point_at_current_sleep_time = 0

    try:
        log.debug('subprocess.Popen() with combined stdout/stderr')
        p = Popen(cmd, stdout=PIPE, stderr=STDOUT, shell=True,
                  universal_newlines=True, preexec_fn=os.setsid)

        if add_to_process_list:
            popper.cli.process_list.append(p.pid)

        log.debug('Reading process output')

        for line in iter(p.stdout.readline, ''):
            line_decoded = b(line)
            log.info(line_decoded[:-1])
        # when we are not writing output to stdout, print dot progress
        if sleep_time < 30 \
                and num_times_point_at_current_sleep_time == 5:
            sleep_time *= 2
            num_times_point_at_current_sleep_time = 0

        num_times_point_at_current_sleep_time += 1

        log.debug('sleeping for {}'.format(sleep_time))

        time.sleep(sleep_time)

        ecode = p.poll()
        log.debug('Code returned by process: {}'.format(ecode))

    except CalledProcessError as ex:
        msg = "Command '{}' failed: {}".format(cmd, ex)
        ecode = ex.returncode
        if not ignore_error:
            log.fail(msg)
        log.info(msg)
    finally:
        log.info()

    return "", ecode


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


def parse(url):
    service_url = None
    service = None
    user = None
    repo = None
    action = None
    if url.startswith('https://'):
        url = url[8:]
        parts = url.split('/')
        service_url = 'https://' + parts[0]
        service = parts[0]
        user = parts[1]
        repo = parts[2]
        tail = '/'.join(parts[2:])
    elif url.startswith('http://'):
        url = url[7:]
        parts = url.split('/')
        service_url = 'http://' + parts[0]
        service = parts[0]
        user = parts[1]
        repo = parts[2]
        tail = '/'.join(parts[2:])
    elif url.startswith('git@'):
        service_url, rest = url.split(':')
        parts = rest.split('/')
        user = parts[0]
        repo = parts[1]
        tail = '/'.join(parts[1:])
        service = service_url[4:]
    elif url.startswith('ssh://'):
        log.fail("The ssh protocol is not supported yet.")
    else:
        service_url = 'https://github.com'
        service = 'github.com'
        parts = url.split('/')
        user = parts[0]
        repo = parts[1]
        tail = '/'.join(parts[1:])
        action = '/'.join(url.split('/')[1:])

    if '@' in tail:
        action_dir = '/'.join(url.split('@')[-2].split('/')[-1:])
        version = url.split('@')[-1]
    elif '@' in action:
        action_dir = '/'.join(action.split('@')[-2].split('/')[-1:])
        version = action.split('@')[-1]
    else:
        action_dir = '/'.join(url.split('/')[2:])
        version = None
    action_dir = os.path.join('./', action_dir)

    return service_url, service, user, repo, action, action_dir, version


def get_parts(url):
    if url.startswith('https://'):
        parts = url[8:].split('/')
    elif url.startswith('http://'):
        parts = url[7:].split('/')
    elif url.startswith('git@'):
        service_url, rest = url.split(':')
        parts = ['github.com'] + rest.split('/')
    elif url.startswith('ssh://'):
        log.fail('The ssh protocol is not supported yet.')
    else:
        parts = ['github.com'] + url.split('/')
    return parts
