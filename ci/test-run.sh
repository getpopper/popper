#!/bin/bash
set -ex

source common-setup.sh

# run
init_test
popper init mypipeone
popper run mypipeone
test -f pipelines/mypipeone/popper_logs/setup.sh.err
test -f pipelines/mypipeone/popper_logs/setup.sh.out
test -f pipelines/mypipeone/popper_logs/run.sh.out
test -f pipelines/mypipeone/popper_logs/run.sh.out
test -f pipelines/mypipeone/popper_logs/post-run.sh.out
test -f pipelines/mypipeone/popper_logs/post-run.sh.out
test -f pipelines/mypipeone/popper_logs/validate.sh.out
test -f pipelines/mypipeone/popper_logs/validate.sh.out
test -f pipelines/mypipeone/popper_logs/teardown.sh.out
test -f pipelines/mypipeone/popper_logs/teardown.sh.out
test -f pipelines/mypipeone/popper_status

# test skipping pipelines
init_test

popper init pipeone --stages=one,two,three
popper init pipetwo --stages=four,five,six

popper run --skip=pipeone

for stage in one two three
do
  test ! -f pipelines/pipeone/popper_logs/$stage.sh.err
  test ! -f pipelines/pipeone/popper_logs/$stage.sh.out
done

for stage in four five six
do
  test -f pipelines/pipetwo/popper_logs/$stage.sh.err
  test -f pipelines/pipetwo/popper_logs/$stage.sh.out
done

