#!/bin/bash
set -ex

source common-setup.sh

# test popper search command
init_test
popper search quiho
popper search data-science --include-readme | grep '>'
test -d ./.cache
popper search --ls
popper search quiho --skip-update
popper search linux --skip-update
popper search --rm popperized
set +e
cat .popper.yml | grep 'github/popperized'
test $? -eq 1
set -e
popper search --add popperized
cat .popper.yml | grep 'github/popperized'
init_test
set +e
popper search quiho --skip-update
test $? -eq 1
set -e

