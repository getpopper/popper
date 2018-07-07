#!/bin/bash
set -ex

source common-setup.sh
# popper reset

init_test
popper init myp
set +e
printf "y\n" | popper reset
cat .popper.yml | grep 'myp'
if [ $? -eq 0 ];
then
  exit 1
fi
set -e

init_test
popper init myp
printf "n\n" | popper reset
cat .popper.yml | grep 'myp'
