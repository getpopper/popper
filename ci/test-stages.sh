#!/bin/bash
set -ex

source common-setup.sh

init_test
popper init mypipeone

# stages
popper stages mypipeone | grep -q setup
popper stages mypipeone | grep -q run
popper stages mypipeone | grep -q post-run
popper stages mypipeone | grep -q validate
popper stages mypipeone | grep -q teardown
popper stages mypipeone --set setup,run,teardown
popper stages mypipeone | grep -q setup
popper stages mypipeone | grep -q run
popper stages mypipeone | grep -q teardown
! popper stages mypipeone | grep -q validate # make sure validate does not show up

# within the pipeline folder, without some stages
init_test
popper init mypipeone
cd pipelines/mypipeone
rm teardown.sh
rm post-run.sh
popper run
test -f popper_logs/setup.sh.err
test -f popper_logs/setup.sh.out
test -f popper_logs/run.sh.out
test -f popper_logs/run.sh.out
test -f popper_logs/validate.sh.out
test -f popper_logs/validate.sh.out
rm -r popper_logs

# run all pipelines
cd /tmp/mypaper
popper init mypipetwo --stages=one,two
popper run
test -f pipelines/mypipeone/popper_logs/setup.sh.err
test -f pipelines/mypipeone/popper_logs/setup.sh.out
test -f pipelines/mypipeone/popper_logs/run.sh.out
test -f pipelines/mypipeone/popper_logs/run.sh.out
test -f pipelines/mypipeone/popper_logs/validate.sh.out
test -f pipelines/mypipeone/popper_logs/validate.sh.out
test -f pipelines/mypipetwo/popper_logs/one.sh.err
test -f pipelines/mypipetwo/popper_logs/one.sh.out
test -f pipelines/mypipetwo/popper_logs/two.sh.out
test -f pipelines/mypipetwo/popper_logs/two.sh.out
test -f pipelines/mypipetwo/popper_status

