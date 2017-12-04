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


def execute(stage, timeout):
    time_limit = time.time() + timeout

    out_fname = 'popper_logs/{}.{}'.format(stage, 'out')
    err_fname = 'popper_logs/{}.{}'.format(stage, 'err')

    sys.stdout.write('Running stage: ' + stage + ' ')

    with open(out_fname, "wb") as outf, open(err_fname, "wb") as errf:
        p = subprocess.Popen('./' + stage, shell=True, stdout=outf, stderr=errf,
                             preexec_fn=os.setsid)

        while p.poll() is None:
            sys.stdout.write('.')

            if time.time() > time_limit:
                os.killpg(os.getpgid(p.pid), signal.SIGTERM)
                sys.stdout.write(' time out!')
                break

            time.sleep(20)

    sys.stdout.write('\n')

    return p.poll()


def check_pipeline(skip, timeout):
    check_output('rm -rf popper_logs/ popper_status', shell=True)
    check_output('mkdir -p popper_logs/', shell=True)

    STATUS = "SUCCESS"

    for stage in stages:

        if not path.isfile(stage):
            continue

        if skip and stage in skip.split(','):
            continue

        ecode = execute(stage, timeout)

        if ecode != 0:
            print("Stage {} failed. Check logs for details.".format(stage))
            STATUS = "FAIL"
            break

        if stage == 'validate.sh':
            STATUS = "GOLD"
            with open('popper_logs/validate.sh.out', 'r') as f:
                validate_output = f.readlines()
                if len(validate_output) == 0:
                    STATUS = "SUCCESS"
                for line in validate_output:
                    if '[true]' not in line:
                        STATUS = "SUCCESS"

    with open('popper_status', 'w') as f:
        f.write(STATUS + '\n')

    print('status: ' + STATUS)


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
    parser.add_argument('--timeout', default=10800, help='Timeout in seconds.')
    parser.add_argument('--skip', default=None, required=False,
                        help='Comma-separated list of stages to skip.')
    args = parser.parse_args()
    sys.stdout = Unbuffered(sys.stdout)

    if path.isdir('./pipelines'):
        for f in os.listdir('pipelines'):
            if not f.startswith('.') and path.isdir('pipelines/' + f):
                print('\nChecking pipeline ' + f)
                os.chdir('pipelines/' + f)
                check_pipeline(args.skip, int(args.timeout))
                os.chdir('../../')
    else:
        check_pipeline(args.skip, int(args.timeout))
