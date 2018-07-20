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

set +e
popper stages
if [ $? -eq 0 ];
then
    exit 1
fi
set -e

init_test
popper init mypipeone
cd pipelines/mypipeone
popper stages | grep -q setup
popper stages | grep -q run
popper stages | grep -q post-run
popper stages | grep -q validate
popper stages | grep -q teardown

# within the pipeline folder, without some stages
init_test
popper init mypipeone
cd pipelines/mypipeone
rm teardown.sh
rm post-run.sh
popper run
test -f popper/host/setup.sh.err
test -f popper/host/setup.sh.out
test -f popper/host/run.sh.out
test -f popper/host/run.sh.out
test -f popper/host/validate.sh.out
test -f popper/host/validate.sh.out
rm -r popper

# run all pipelines
cd /tmp/mypaper
popper init mypipetwo --stages=one,two
popper run
test -f pipelines/mypipeone/popper/host/setup.sh.err
test -f pipelines/mypipeone/popper/host/setup.sh.out
test -f pipelines/mypipeone/popper/host/run.sh.out
test -f pipelines/mypipeone/popper/host/run.sh.out
test -f pipelines/mypipeone/popper/host/validate.sh.out
test -f pipelines/mypipeone/popper/host/validate.sh.out
test -f pipelines/mypipetwo/popper/host/one.sh.err
test -f pipelines/mypipetwo/popper/host/one.sh.out
test -f pipelines/mypipetwo/popper/host/two.sh.out
test -f pipelines/mypipetwo/popper/host/two.sh.out
test -f pipelines/mypipetwo/popper/host/popper_status

