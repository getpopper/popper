import os
import sys
import threading
import time
from subprocess import PIPE, STDOUT, CalledProcessError, Popen, check_output
import click
import popper.cli


def fail(msg, colorize=True):
    """Prints the error message on the terminal."""
    click.echo(click.style('ERROR: ', bg='red', fg='white') +
               click.style(msg, bold=True),
               err=True, nl=False, color=True)
    sys.exit(1)


def warn(msg, colorize=True):
    click.echo(click.style('WARNING: ', bg='yellow', fg='black', bold=True) +
               click.style(msg, fg='yellow', bold=True),
               err=True, nl=False, color=True)


def info(msg, prefix='', action='', colorize=True):
    """Prints the message on the terminal."""
    click.echo(click.style(prefix, fg='green', bold=True) +
               click.style(action, fg='blue', bold=True) +
               click.style(msg), nl=False, color=colorize)


def print_yaml(msg, **styles):
    """Prints the messages in YAML's block format'\033[0m' +. """
    click.secho(yaml.safe_dump(msg, default_flow_style=False), **styles)


def exec_cmd(cmd, verbose=False, debug=False, ignore_error=False,
             log_file=None, dry_run=False, add_to_process_list=False):

    # If dry_run is True, I don't want the command to be executed
    # just an empty return

    if dry_run:
        return "", 0    # No error occurred

    # the main logic is the following:
    #
    # 1) verbose=False and log_file=None
    #      ==> don't write anything to stdout/log
    # 2) verbose=True and log_file=None
    #      ==> combine stdout/stderr in the same stream and print it to stdout
    # 3) verbose=False and log_file not None
    #      ==> write two files, one .out and one .err
    # 4) verbose=True and log_file not None
    #      ==> combine stdout/stderr, write to stdout and to a SINGLE log file

    # internal nested function to make treatment of stdout 2 and 3 compatible
    def b(t):
        if isinstance(t, bytes):
            return t.decode('utf-8')
        return t

    ecode = None
    # quick shortcut for 1) above
    if not verbose and not log_file:
        out = ""
        if debug:
            info(prefix='DEBUG:',
                 msg=' Using subprocess.check_output() for {}\n'.format(cmd))
        try:
            out = check_output(cmd, shell=True, stderr=PIPE,
                               universal_newlines=True)
            ecode = 0
        except CalledProcessError as ex:
            ecode = ex.returncode
            if debug:
                info(prefix='DEBUG:',
                     msg='Catched exception: {}\n'.format(ex))
            if not ignore_error:
                fail("Command '{}' failed: {}\n".format(cmd, ex))
        return b(out).strip(), ecode

    sleep_time = 0.25
    num_times_point_at_current_sleep_time = 0
    outf = None
    errf = None

    if log_file:
        if verbose:
            if debug:
                info(prefix='\nDEBUG:',
                     msg='Creating file for combined stdout/stderr\n')
            outf = open(log_file + '.log', 'w')
        else:
            if debug:
                info(prefix='\nDEBUG:',
                     msg=' Creating separate files for stdout/stderr\n')
            outf = open(log_file + '.out', 'w')
            errf = open(log_file + '.err', 'w')

    try:
        if verbose:
            if debug:
                info(prefix='DEBUG:',
                     msg=' subprocess.Popen() with combined stdout/stderr\n')
            p = Popen(cmd, stdout=PIPE, stderr=STDOUT, shell=True,
                      universal_newlines=True, preexec_fn=os.setsid)
        else:
            if debug:
                info(prefix='DEBUG:',
                     msg=' subprocess.Popen() with separate stdout/stderr\n')
            p = Popen(cmd, stdout=outf, stderr=errf, shell=True,
                      universal_newlines=True, preexec_fn=os.setsid)

        if add_to_process_list:
            popper.cli.process_list.append(p.pid)

        if debug:
            info(prefix='\nDEBUG:', msg=' Reading process output\n')

        while ecode is None:

            if verbose:
                # read until end of file (when process stops)
                for line in iter(p.stdout.readline, ''):
                    line_decoded = b(line)
                    info(line_decoded)
                    if log_file:
                        outf.write(line)
            else:
                # when we are not writing output to stdout, print dot progress
                if sleep_time < 30 \
                        and num_times_point_at_current_sleep_time == 5:
                    sleep_time *= 2
                    num_times_point_at_current_sleep_time = 0

                num_times_point_at_current_sleep_time += 1

                if debug:
                    info(prefix='DEBUG:',
                         msg=' sleeping for {}\n'.format(sleep_time))
                else:
                    info('.')

                time.sleep(sleep_time)

            ecode = p.poll()
            if debug:
                info(prefix='DEBUG:', msg=' Code returned by process: {}\n'.format(ecode))

    except CalledProcessError as ex:
        msg = "Command '{}' failed: {}\n".format(cmd, ex)
        ecode = ex.returncode
        if not ignore_error:
            fail(msg)
        info(msg)
    finally:
        info('\n')
        if outf:
            outf.close()
        if errf:
            errf.close()

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
        fail(
            "Files {} or {} not found.\n".format("./main.workflow",
                                                 ".github/main.workflow"))
    if not os.path.isfile(wfile):
        fail("File {} not found.\n".format(wfile))
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
        fail("The ssh protocol is not supported yet.")
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

    return (service_url, service, user, repo, action, action_dir, version)


def get_parts(url):
    if url.startswith('https://'):
        parts = url[8:].split('/')
    elif url.startswith('http://'):
        parts = url[7:].split('/')
    elif url.startswith('git@'):
        service_url, rest = url.split(':')
        parts = ['github.com'] + rest.split('/')
    elif url.startswith('ssh://'):
        fail('The ssh protocol is not supported yet.')
    else:
        parts = ['github.com'] + url.split('/')
    return parts
