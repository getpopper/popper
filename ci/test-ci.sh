#!/bin/bash
set -ex

source common-setup.sh

init_test

popper ci --service travis
test -f .travis.yml

popper ci --service circle
test -f .circleci/config.yml

popper ci --service jenkins
test -f Jenkinsfile

popper ci --service gitlab
test -f .gitlab-ci.yml


# test skipping
init_test

popper init pipeone --stages=one,two,three
popper init pipetwo --stages=four,five,six
popper init pipethree --stages=seven

popper ci --service travis --skip=pipetwo,pipethree

cat .travis.yml | grep 'popper run --skip=pipetwo,pipethree'

popper ci --service travis --skip=pipetwo,pipethree --requirement-level warn

cat .travis.yml | grep 'popper run --skip=pipetwo,pipethree --requirement-level warn'
