#!/usr/bin/env python

import argparse
import os
import subprocess
import time
import signal
import sys

from subprocess import check_output
from os import path

stages = ['setup.sh', 'run.sh', 'post-run.sh', 'validate.sh', 'teardown.sh']


def execute(stage, timeout, docker):
    time_limit = time.time() + timeout

    docker_flag = ""

    if docker:
        docker_flag = docker + "_"

    out_fname = docker_flag + "popper_logs/{}.{}".format(stage, 'out')
    err_fname = docker_flag + "popper_logs/{}.{}".format(stage, 'err')

    sys.stdout.write('Running stage: ' + stage + ' ')

    with open(out_fname, "wb") as outf, open(err_fname, "wb") as errf:
        p = subprocess.Popen('./' + stage, shell=True, stdout=outf,
                             stderr=errf, preexec_fn=os.setsid)

        while p.poll() is None:
            sys.stdout.write('.')

            if time.time() > time_limit:
                os.killpg(os.getpgid(p.pid), signal.SIGTERM)
                sys.stdout.write(' time out!')
                break

            time.sleep(20)

    sys.stdout.write('\n')

    return p.poll()


def check_pipeline(skip, timeout, docker, exit_on_fail=True,
                   show_logs_on_fail=True):

    docker_flag = ""

    if docker:
        docker_flag = docker + "_"

    check_output("rm -rf " + docker_flag + "popper_logs/ popper_status",
                 shell=True)
    check_output("mkdir " + docker_flag + "popper_logs/", shell=True)

    STATUS = "SUCCESS"

    for stage in stages:

        if not path.isfile(stage):
            continue

        if skip and stage in skip.split(','):
            continue

        ecode = execute(stage, timeout, docker)

        if ecode != 0:
            print("Stage {} failed.".format(stage))
            STATUS = "FAIL"
            if show_logs_on_fail:
                print("Logs for {}:.".format(stage))
                for t in ['.err', '.out']:
                    with open(docker_flag +
                              "popper_logs/{}{}".format(stage, t), 'r') as f:
                        print(f.read())
            break

        if stage == 'validate.sh':
            STATUS = "GOLD"
            with open(docker_flag + "popper_logs/validate.sh.out", 'r') as f:
                validate_output = f.readlines()
                if len(validate_output) == 0:
                    STATUS = "SUCCESS"
                for line in validate_output:
                    if '[true]' not in line:
                        STATUS = "SUCCESS"

    with open('popper_status', 'w') as f:
        f.write(STATUS + '\n')

    print('status: ' + STATUS)

    if STATUS == 'FAIL' and exit_on_fail:
        sys.exit(1)

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


class Unbuffered(object):
    def __init__(self, stream):
        self.stream = stream

    def write(self, data):
        self.stream.write(data)
        self.stream.flush()

    def __getattr__(self, attr):
        return getattr(self.stream, attr)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--timeout', default="10800s",
                        help='Timeout in seconds.')
    parser.add_argument('--docker', default=None,
                        help='Timeout in seconds.')
    parser.add_argument('--skip', default=None, required=False,
                        help='Comma-separated list of stages to skip.')
    args = parser.parse_args()
    sys.stdout = Unbuffered(sys.stdout)

    timeout = parse_timeout(args.timeout)

    if path.isdir('./pipelines'):
        for f in os.listdir('pipelines'):
            if not f.startswith('.') and path.isdir('pipelines/' + f):
                print('\nChecking pipeline ' + f)
                os.chdir('pipelines/' + f)
                check_pipeline(args.skip, timeout, args.docker)
                os.chdir('../../')
    else:
        check_pipeline(args.skip, timeout, args.docker)
