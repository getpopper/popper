#!/bin/bash
set -ex

source common-setup.sh

sleep 10

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
if [ $? -eq 0 ];
then
  exit 1
fi
set -e

popper search --add popperized
cat .popper.yml | grep 'github/popperized'
init_test

set +e
popper search quiho --skip-update
if [ $? -eq 0 ];
then
  exit 1
fi
set -e

