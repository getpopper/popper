import click
import os
import signal
import subprocess
import sys
import time
import yaml

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


def get_items(dict_object):
    """Python 2/3 compatible way of iterating over a dictionary"""
    for key in dict_object:
        yield key, dict_object[key]


def get_project_root():
    """Tries to find the root of the project with the following heuristic:

      - Find the .git folder in cwd

    Returns:
        project_root (str): The fully qualified path to the root of project.
    """
    base, _ = exec_cmd('git rev-parse --show-toplevel', ignore_error=True)

    if not base:
        fail("Unable to find root of project. Initialize repository first.")

    return base


def write_config(config):
    """Writes config to .popper.yml file."""
    config_filename = os.path.join(get_project_root(), '.popper.yml')

    with open(config_filename, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, Dumper=noalias_dumper)


def is_popperized():
    """Determines if the current repo has already been popperized by checking
    whether the '.popper.yml' file on the root of the project exits.

    Returns:
       True if the '.popper.yml' exists, False otherwise.
    """
    config_filename = os.path.join(get_project_root(), '.popper.yml')
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


def parse_timeout(timeout):
    """Takes timeout as string and parses it to obtain the number of seconds.
    Generates valid error if proper format is not used.

    Returns:
        Value of timeout in seconds (float).
    """
    time_out = 0
    to_seconds = {"s": 1, "m": 60, "h": 3600}
    try:
        time_out = float(timeout)
    except ValueError:
        literals = timeout.split()
        for literal in literals:
            unit = literal[-1].lower()
            try:
                value = float(literal[:-1])
            except ValueError:
                fail("invalid timeout format used. "
                     "See popper run --help for more.")
            try:
                time_out += value * to_seconds[unit]
            except KeyError:
                fail("invalid timeout format used. "
                     "See popper run --help for more.")

    return time_out


def exec_cmd(cmd, verbose=False, ignore_error=False, print_progress_dot=False,
             write_logs=False, log_filename=None, timeout=10800):

    # quick shortcut for just running without verbose, logging and progress dot
    if not verbose and not write_logs and not print_progress_dot:
        try:
            out = subprocess.check_output(cmd, shell=True)
        except subprocess.CalledProcessError as ex:
            if not ignore_error:
                fail("Command '{}' failed: {}\n".format(cmd, ex))
        return out.strip(), 0

    output = ""
    ecode = 1
    time_limit = time.time() + timeout
    sleep_time = 0.25
    num_times_point_at_current_sleep_time = 0
    outf = None
    errf = None

    if write_logs:
        outf = open(log_filename + '.out', 'w')
        errf = open(log_filename + '.err', 'w')

    try:
        p = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            shell=True, preexec_fn=os.setsid)

        while not p.poll():
            out = p.stdout.readline().decode("utf-8")
            err = p.stderr.readline().decode("utf-8")
            if out:
                output += out
                if verbose:
                    info(out)
                if write_logs:
                    outf.write(out)
            if err:
                sys.stderr.write(err)
                if write_logs:
                    errf.write(err)

            if timeout != 0.0 and time.time() > time_limit:
                os.killpg(os.getpgid(p.pid), signal.SIGTERM)
                info(' time out!\n')
                break

            if sleep_time < 30 \
                    and num_times_point_at_current_sleep_time == 5:
                sleep_time *= 2
                num_times_point_at_current_sleep_time = 0

            if not verbose and print_progress_dot:
                sys.stdout.write('.')
                num_times_point_at_current_sleep_time += 1

            time.sleep(sleep_time)

        ecode = p.poll()

    except subprocess.CalledProcessError as ex:
        if not ignore_error:
            fail("Command '{}' failed: {}\n".format(cmd, ex))
    finally:
        if write_logs:
            outf.close()
            errf.close()

    return output, ecode


def get_git_files():
    """Used to return a list of files that are being tracked by
    git.

    Returns:
        files (list) : list of git tracked files
    """
    gitfiles, _ = exec_cmd("git ls-files")
    return gitfiles.split("\n")
