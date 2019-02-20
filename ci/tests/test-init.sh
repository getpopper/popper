#!/bin/bash
set -ex
source common-setup.sh
init_test
test -f .popper.yml
cat .popper.yml | grep 'version: 2'
