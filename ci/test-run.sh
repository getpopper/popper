#!/bin/bash
set -ex

source common-setup.sh

# run
init_test
popper init mypipeone
popper run mypipeone
test -f pipelines/mypipeone/popper/host/setup.sh.err
test -f pipelines/mypipeone/popper/host/setup.sh.out
test -f pipelines/mypipeone/popper/host/run.sh.err
test -f pipelines/mypipeone/popper/host/run.sh.out
test -f pipelines/mypipeone/popper/host/post-run.sh.err
test -f pipelines/mypipeone/popper/host/post-run.sh.out
test -f pipelines/mypipeone/popper/host/validate.sh.err
test -f pipelines/mypipeone/popper/host/validate.sh.out
test -f pipelines/mypipeone/popper/host/teardown.sh.err
test -f pipelines/mypipeone/popper/host/teardown.sh.out
test -f pipelines/mypipeone/popper/host/popper_status

# test skipping stages
init_test
popper init pipeone --stages=one,two,three,four

popper run pipeone --skip=one,two

for stage in one two
do
  test ! -f pipelines/pipeone/popper/host/$stage.sh.err
  test ! -f pipelines/pipeone/popper/host/$stage.sh.out
done

for stage in three four
do
  test -f pipelines/pipeone/popper/host/$stage.sh.err
  test -f pipelines/pipeone/popper/host/$stage.sh.out
done

# test skipping based on commit
init_test

git config user.email "<>"
git config user.name "test travis ci"

popper init --stages=setup mypipeone
popper init --stages=setup mypipetwo
popper init --stages=setup mypipethree

git add .
git commit --allow-empty -m "popper:whitelist[mypipeone] this is a test"

popper run --no-badge-update

test -f pipelines/mypipeone/popper/host/setup.sh.err
test -f pipelines/mypipeone/popper/host/setup.sh.out
test ! -f pipelines/mypipetwo/popper/host/setup.sh.err
test ! -f pipelines/mypipetwo/popper/host/setup.sh.out
test ! -f pipelines/mypipethree/popper/host/setup.sh.err
test ! -f pipelines/mypipethree/popper/host/setup.sh.out

git clean -df

git commit --allow-empty -m "popper:whitelist[mypipeone,mypipetwo] this is a test"

popper run --no-badge-update

test -f pipelines/mypipeone/popper/host/setup.sh.err
test -f pipelines/mypipeone/popper/host/setup.sh.out
test -f pipelines/mypipetwo/popper/host/setup.sh.err
test -f pipelines/mypipetwo/popper/host/setup.sh.out
test ! -f pipelines/mypipethree/popper/host/setup.sh.err
test ! -f pipelines/mypipethree/popper/host/setup.sh.out

git clean -df

git commit --allow-empty -m "popper:skip[mypipeone] this is a test"

popper run --no-badge-update

test ! -f pipelines/mypipeone/popper/host/setup.sh.err
test ! -f pipelines/mypipeone/popper/host/setup.sh.out
test -f pipelines/mypipetwo/popper/host/setup.sh.err
test -f pipelines/mypipetwo/popper/host/setup.sh.out
test -f pipelines/mypipethree/popper/host/setup.sh.err
test -f pipelines/mypipethree/popper/host/setup.sh.out

git clean -df

git commit --allow-empty -m "popper:skip[mypipeone,mypipetwo] this is a test"

popper run --no-badge-update

test ! -f pipelines/mypipeone/popper/host/setup.sh.err
test ! -f pipelines/mypipeone/popper/host/setup.sh.out
test ! -f pipelines/mypipetwo/popper/host/setup.sh.err
test ! -f pipelines/mypipetwo/popper/host/setup.sh.out
test -f pipelines/mypipethree/popper/host/setup.sh.err
test -f pipelines/mypipethree/popper/host/setup.sh.out
