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
