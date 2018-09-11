#!/bin/bash
set -ex

source common-setup.sh

init_test
popper init samples/exp1
popper mv exp1 exp2
cat .popper.yml | grep 'samples/exp2'
test -d samples/exp2
test -f samples/exp2/setup.sh
test -f samples/exp2/run.sh
test -f samples/exp2/post-run.sh
test -f samples/exp2/validate.sh
test -f samples/exp2/teardown.sh

popper mv exp2 samples2/exp2
cat .popper.yml | grep 'samples2/exp2'
test -d samples2/exp2
test -f samples2/exp2/setup.sh
test -f samples2/exp2/run.sh
test -f samples2/exp2/post-run.sh
test -f samples2/exp2/validate.sh
test -f samples2/exp2/teardown.sh

popper mv exp2 samples3/exp1
cat .popper.yml | grep 'samples3/exp1'
test -d samples3/exp1
test -f samples3/exp1/setup.sh
test -f samples3/exp1/run.sh
test -f samples3/exp1/post-run.sh
test -f samples3/exp1/validate.sh
test -f samples3/exp1/teardown.sh

set +e
popper mv exp5 exp1
if [ $? -eq 0];
then
    exit 1
fi

popper mv samples5/exp1 exp1
if [ $? -eq 0];
then
    exit 1
fi
set -e
