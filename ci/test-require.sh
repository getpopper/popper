#!/bin/bash
set -ex

source common-setup.sh

if [ -f /.dockerenv ]; then
  output_dir=popper
else
  output_dir=popper/host
fi

init_test
popper init mypipeone --stages=stageone
popper init mypipetwo --stages=stageone

popper require mypipeone -e TEST_VAR_ONE
popper require mypipeone -e TEST_VAR_TWO
popper require mypipetwo -e TEST_VAR_TWO
cat .popper.yml | grep "\- TEST_VAR_ONE"
cat .popper.yml | grep "\- TEST_VAR_TWO"


unset TEST_VAR_ONE
export TEST_VAR_TWO=1

# test erroring

# fail by default
set +e
popper run
if [ $? -eq 0 ];
then
  exit 1
fi
set -e


# fail explicitly
set +e
popper run --requirement-level fail
if [ $? -eq 0 ];
then
  exit 1
fi
set -e


# warn on missing reqs
popper run --requirement-level warn

test ! -d pipelines/mypipeone/popper_logs

test -d pipelines/mypipetwo/$output_dir
test -f pipelines/mypipetwo/$output_dir/stageone.sh.out
test -f pipelines/mypipetwo/$output_dir/stageone.sh.err

# ignore warning
popper run --requirement-level ignore

test -d pipelines/mypipeone/$output_dir
test -f pipelines/mypipeone/$output_dir/stageone.sh.out
test -f pipelines/mypipeone/$output_dir/stageone.sh.err

test -d pipelines/mypipetwo/$output_dir
test -f pipelines/mypipetwo/$output_dir/stageone.sh.out
test -f pipelines/mypipetwo/$output_dir/stageone.sh.err


# test for running single pipe

# fail by default
set +e
popper run mypipeone
if [ $? -eq 0 ];
then
  exit 1
fi
set -e


# fail explicitly
set +e
popper run mypipeone --requirement-level fail
if [ $? -eq 0 ];
then
  exit 1
fi
set -e

rm -rf pipelines/mypipeone/$output_dir

# warn on missing reqs
popper run mypipeone --requirement-level warn

test ! -d pipelines/mypipeone/$output_dir

# ignore warning
popper run mypipeone --requirement-level ignore

test -d pipelines/mypipeone/$output_dir
test -f pipelines/mypipeone/$output_dir/stageone.sh.out
test -f pipelines/mypipeone/$output_dir/stageone.sh.err

# test success
export TEST_VAR_ONE=1
popper run mypipeone

# test running from CWD

rm -rf pipelines/mypipeone/$output_dir
cd pipelines/mypipeone

# success
popper run

rm -rf popper_logs
unset TEST_VAR_ONE

# Failure
set +e
popper run
if [ $? -eq 0 ];
then
  exit 1
fi
set -e

# test clearing requirements
popper require mypipeone --clear

popper run mypipeone

