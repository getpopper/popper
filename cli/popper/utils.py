import click
import os
import sys
import time
import yaml
import threading
from subprocess import check_output, CalledProcessError, PIPE, Popen, STDOUT

noalias_dumper = yaml.dumper.SafeDumper
noalias_dumper.ignore_aliases = lambda self, data: True

init_config = {
    'metadata': {
        'access_right': "open",
        'license': "CC-BY-4.0",
        'upload_type': "publication",
        'publication_type': "article"
    },
    'search_sources': [
        "popperized"
    ],
    'version': 2,
}

gitignore_content = ".pipeline_cache.yml\npopper/\n"

main_workflow_content = """
workflow "example" {
  on = "push"
  resolves = "example action"
}

action "github official action" {
  uses = "actions/bin/sh@master"
  args = ["ls"]
}

action "docker action" {
  uses = "docker://node:6"
  args = ["node --version"]
}

action "example action" {
  uses = "./%s"
  args = ["github.com"]
}
"""

dockerfile_content = """
FROM debian:stable-slim

LABEL "name"="curl"
LABEL "maintainer"="GitHub Actions <support+actions@github.com>"
LABEL "version"="1.0.0"

LABEL "com.github.actions.name"="cURL for GitHub Actions"
LABEL "com.github.actions.description"="Runs cURL in an Action"
LABEL "com.github.actions.icon"="upload-cloud"
LABEL "com.github.actions.color"="green"


COPY entrypoint.sh /entrypoint.sh

RUN apt-get update && \
    apt-get install curl -y && \
    apt-get clean -y

ENTRYPOINT ["sh", "/entrypoint.sh"]
"""

entrypoint_content = """
#!/bin/sh
set -e

sh -c "curl $*"
"""

readme_content = "Executes cURL with arguments listed in the Action's args."


def get_items(dict_object):
    """Python 2/3 compatible way of iterating over a dictionary"""
    for key in dict_object:
        yield key, dict_object[key]


def write_config(rootfolder, config):
    """Writes config to .popper.yml file."""
    config_filename = os.path.join(rootfolder, '.popper.yml')

    with open(config_filename, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, Dumper=noalias_dumper)


def is_popperized(rootfolder):
    """Determines if the current repo has already been popperized by checking
    whether the '.popper.yml' file on the root of the project exits.

    Returns:
       True if the '.popper.yml' exists, False otherwise.
    """
    config_filename = os.path.join(rootfolder, '.popper.yml')
    return os.path.isfile(config_filename)


def fail(msg):
    """Prints the error message on the terminal."""
    click.secho('ERROR: ' + msg, fg='red', bold=True, err=True, nl=False)
    sys.exit(1)


def warn(msg):
    click.secho('WARNING: ' + msg, bold=True, fg='red', err=True, nl=False)


def info(msg, **styles):
    """Prints the message on the terminal."""
    click.secho(msg, nl=False, **styles)


def print_yaml(msg, **styles):
    """Prints the messages in YAML's block format. """
    click.secho(yaml.safe_dump(msg, default_flow_style=False), **styles)


def exec_cmd(cmd, verbose=False, debug=False, ignore_error=False,
             log_file=None, dry_run=False):

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

    # quick shortcut for 1) above
    if not verbose and not log_file:
        out = ""
        if debug:
            info('DEBUG: Using subprocess.check_output() for {}\n'.format(cmd))
        try:
            out = check_output(cmd, shell=True, stderr=PIPE,
                               universal_newlines=True)
        except CalledProcessError as ex:
            if debug:
                info('DEBUG: Catched exception: {}\n'.format(ex))
            if not ignore_error:
                fail("Command '{}' failed: {}\n".format(cmd, ex))
        return b(out).strip(), 0

    sleep_time = 0.25
    num_times_point_at_current_sleep_time = 0
    ecode = None
    outf = None
    errf = None

    if log_file:
        if verbose:
            if debug:
                info('\nDEBUG: Creating file for combined stdout/stderr\n')
            outf = open(log_file + '.log', 'w')
        else:
            if debug:
                info('\nDEBUG: Creating separate files for stdout/stderr\n')
            outf = open(log_file + '.out', 'w')
            errf = open(log_file + '.err', 'w')

    try:
        if verbose:
            if debug:
                info('DEBUG: subprocess.Popen() with combined stdout/stderr\n')
            p = Popen(cmd, stdout=PIPE, stderr=STDOUT, shell=True,
                      universal_newlines=True)
        else:
            if debug:
                info('DEBUG: subprocess.Popen() with separate stdout/stderr\n')
            p = Popen(cmd, stdout=outf, stderr=errf, shell=True,
                      universal_newlines=True)

        if debug:
            info('DEBUG: Reading process output\n')

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
                    info('DEBUG: sleeping for {}\n'.format(sleep_time))
                else:
                    info('.')

                time.sleep(sleep_time)

            ecode = p.poll()
            if debug:
                info('DEBUG: Code returned by process: {}\n'.format(ecode))

    except CalledProcessError as ex:
        msg = "Command '{}' failed: {}\n".format(cmd, ex)
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


def get_git_files():
    """Used to return a list of files that are being tracked by
    git.

    Returns:
        files (list) : list of git tracked files
    """
    gitfiles, _ = exec_cmd("git ls-files")
    return gitfiles.split("\n")


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
