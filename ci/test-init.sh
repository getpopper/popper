#!/bin/bash
set -ex

source common-setup.sh

# arbitrary stages and envs
init_test
popper init --stages=one,two,three --envs=host,ubuntu-xenial pipetwo
popper init --stages=one,two,teardown sample_exp

set +e
popper init --stages=one,teardown,three sample_exp2
if [ $? -eq 0 ];
then
  exit 1
fi
set -e

cat .popper.yml | grep '\- host'
cat .popper.yml | grep '\- ubuntu-xenial'
cat .popper.yml | grep '\- one'
cat .popper.yml | grep '\- two'
cat .popper.yml | grep '\- three'
test -f pipelines/pipetwo/one.sh
test -f pipelines/pipetwo/two.sh
test -f pipelines/pipetwo/three.sh

# initializing a pipeline in a custom folder
popper init samples/experiment
cat .popper.yml | grep 'samples/experiment'
test -d samples/experiment
test -f samples/experiment/setup.sh
test -f samples/experiment/run.sh
test -f samples/experiment/post-run.sh
test -f samples/experiment/validate.sh
test -f samples/experiment/teardown.sh
