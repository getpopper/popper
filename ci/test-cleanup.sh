#!/bin/bash
set -ex

source common-setup.sh

# cleanup command
init_test
popper init mypipetwo
popper init mypipethree
rm pipelines/mypipetwo/teardown.sh
rm pipelines/mypipetwo/post-run.sh
rm -rf pipelines/mypipethree
cat .popper.yml | grep mypipethree
popper stages mypipetwo | grep teardown
popper stages mypipetwo | grep post-run
popper cleanup
! cat .popper.yml | grep mypipethree
! popper stages mypipetwo | grep teardown
! popper stages mypipetwo | grep post-run

