#!/bin/bash
set -ex

source common-setup.sh

popper --help

init_test
ls
test -f .popper.yml

# default values

popper init paper
cat .popper.yml | grep 'path: paper'
test -f paper/build.sh

popper init pipeone
cat .popper.yml | grep '\- host'
cat .popper.yml | grep 'path: pipelines/pipeone'
test -f pipelines/pipeone/setup.sh
test -f pipelines/pipeone/run.sh
test -f pipelines/pipeone/post-run.sh
test -f pipelines/pipeone/validate.sh
test -f pipelines/pipeone/teardown.sh

# user-friendly timeout values
popper run --timeout 2.5
popper run --timeout 10s
popper run --timeout 0.5m
popper run --timeout .01h
popper run --timeout "1m 10s"

