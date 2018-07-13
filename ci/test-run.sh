#!/bin/bash
set -ex

source common-setup.sh

# run
init_test
popper init mypipeone
popper run mypipeone
test -f pipelines/mypipeone/popper_logs/setup.sh.err
test -f pipelines/mypipeone/popper_logs/setup.sh.out
test -f pipelines/mypipeone/popper_logs/run.sh.err
test -f pipelines/mypipeone/popper_logs/run.sh.out
test -f pipelines/mypipeone/popper_logs/post-run.sh.err
test -f pipelines/mypipeone/popper_logs/post-run.sh.out
test -f pipelines/mypipeone/popper_logs/validate.sh.err
test -f pipelines/mypipeone/popper_logs/validate.sh.out
test -f pipelines/mypipeone/popper_logs/teardown.sh.err
test -f pipelines/mypipeone/popper_logs/teardown.sh.out
test -f pipelines/mypipeone/popper_status

# test skipping stages
init_test
popper init pipeone --stages=one,two,three,four

popper run pipeone --skip=one,two

for stage in one two
do
  test ! -f pipelines/pipeone/popper_logs/$stage.sh.err
  test ! -f pipelines/pipeone/popper_logs/$stage.sh.out
done

for stage in three four
do
  test -f pipelines/pipeone/popper_logs/$stage.sh.err
  test -f pipelines/pipeone/popper_logs/$stage.sh.out
done

# test skipping pipelines
init_test

popper init pipeone --stages=one,two,three
popper init pipetwo --stages=four,five,six

popper run --skip=pipeone,pipetwo:five

for stage in one two three
do
  test ! -f pipelines/pipeone/popper_logs/$stage.sh.err
  test ! -f pipelines/pipeone/popper_logs/$stage.sh.out
done

for stage in four six
do
  test -f pipelines/pipetwo/popper_logs/$stage.sh.err
  test -f pipelines/pipetwo/popper_logs/$stage.sh.out
done

test ! -f pipelines/pipetwo/popper_logs/five.sh.err
test ! -f pipelines/pipetwo/popper_logs/five.sh.out

# test run in docker
init_test

popper init mypipeone

popper env mypipeone --add alpine-3.4,debian-9,centos-7.4

popper env mypipeone --rm host

popper run mypipeone

# test skipping based on commit
init_test

git config user.email "<>"
git config user.name "test travis ci"

popper init mypipeone
popper init mypipetwo

git commit --allow-empty -m "popper:skip this is a test"

popper run

test ! -f pipelines/mypipeone/popper_logs/setup.sh.err
test ! -f pipelines/mypipeone/popper_logs/setup.sh.out

test ! -f pipelines/mypipetwo/popper_logs/setup.sh.err
test ! -f pipelines/mypipetwo/popper_logs/setup.sh.out


git commit --allow-empty -m "popper:whitelist[mypipeone] this is a test"
popper run

test -f pipelines/mypipeone/popper_logs/setup.sh.err
test -f pipelines/mypipeone/popper_logs/setup.sh.out

test ! -f pipelines/mypipetwo/popper_logs/setup.sh.err
test ! -f pipelines/mypipetwo/popper_logs/setup.sh.out



