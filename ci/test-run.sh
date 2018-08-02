#!/bin/bash
source common-setup.sh

set -ex

# run
init_test
popper init mypipeone
popper run mypipeone

for s in setup run post-run validate teardown; do
  test -f pipelines/mypipeone/$output_dir/$s.sh.err
  test -f pipelines/mypipeone/$output_dir/$s.sh.out
done
test -f pipelines/mypipeone/$output_dir/popper_status


# test skipping pipelines
init_test
popper init pipeone --stages=one
popper init pipetwo --stages=two,three

popper run --skip=pipeone

pipe_didnt_run pipeone
pipe_ran pipetwo


# test skipping stages
init_test
popper init pipeone --stages=one,two,three,four

popper run pipeone --skip=one,two

for stage in one two
do
  stage_didnt_run pipeone $stage
done

for stage in three four
do
  stage_ran pipeone $stage
done


# test skippint with pipeline:stage pairs
init_test
popper init pipeone --stages=one,two,three,four
popper init pipetwo --stages=two,three

popper run --skip=pipeone:one,pipeone:two

for stage in one two
do
  stage_didnt_run pipeone $stage
done

for stage in three four
do
  stage_ran pipeone $stage
done

pipe_ran pipetwo


# test skipping based on commit
init_test

if [ -z $CI ]; then
  ci_not_set=1
  export CI=1
fi

git config user.email "<>"
git config user.name "test travis ci"

popper init --stages=setup mypipeone
popper init --stages=setup mypipetwo
popper init --stages=setup mypipethree

git add .
git commit --allow-empty -m "popper:whitelist[mypipeone] this is a test"
popper run --no-badge-update

stage_ran mypipeone setup
stage_didnt_run mypipetwo setup
stage_didnt_run mypipethree setup


git clean -dxf
git commit --allow-empty -m "popper:whitelist[mypipeone,mypipetwo] this is a test"
popper run --no-badge-update

stage_ran mypipeone setup
stage_ran mypipetwo setup
stage_didnt_run mypipethree setup


git clean -dxf
git commit --allow-empty -m "popper:skip[mypipeone] this is a test"
popper run --no-badge-update

stage_didnt_run mypipeone setup
stage_ran mypipetwo setup
stage_ran mypipethree setup


git clean -dxf
git commit --allow-empty -m "popper:skip[mypipeone,mypipetwo] this is a test"
popper run --no-badge-update

stage_didnt_run mypipeone setup
stage_didnt_run mypipetwo setup
stage_ran mypipethree setup


if [ -z $ci_not_set ]; then
  unset CI
fi
