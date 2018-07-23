#!/bin/bash
set -ex

source common-setup.sh

sleep 10

# popper add
init_test
popper add popperized/swc-lesson-pipelines/co2-emissions
test -d pipelines/co2-emissions
test -f pipelines/co2-emissions/README.md
test -f pipelines/co2-emissions/run.sh
test -f pipelines/co2-emissions/setup.sh
test -f pipelines/co2-emissions/validate.sh

init_test
popper add popperized/swc-lesson-pipelines/co2-emissions foo/emissions
test -d foo/emissions
cat .popper.yml | grep 'emissions:'
cat .popper.yml | grep 'path: foo/emissions'
test -f foo/emissions/run.sh

init_test
popper add popperized/swc-lesson-pipelines/co2-emissions foo
test -d pipelines/foo
cat .popper.yml | grep 'foo:'
cat .popper.yml | grep 'path: pipelines/foo'
test -f pipelines/foo/run.sh

init_test
popper add popperized/swc-lesson-pipelines/co2-emissions foo/
test -d foo/
cat .popper.yml | grep 'foo:'
cat .popper.yml | grep 'path: foo'
test -f foo/run.sh

# info command
popper info popperized/popper-readthedocs-examples/docker-data-science | grep 'url'

# popper add --branch
init_test
popper add popperized/swc-lesson-pipelines/co2-emissions --branch revert-1-master
test -d pipelines/co2-emissions
test -d pipelines/co2-emissions/scripts
test -f pipelines/co2-emissions/README.md
test -f pipelines/co2-emissions/run.sh
test -f pipelines/co2-emissions/setup.sh
test -f pipelines/co2-emissions/validate.sh
