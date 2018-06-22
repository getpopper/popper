#!/bin/bash
set -ex

source common-setup.sh
# popper reset

init_test
popper init myp
set +e
popper reset
cat .popper.yml | grep 'myp'
test $? -ne 0
set -e

