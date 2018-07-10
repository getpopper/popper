#!/bin/bash
set -ex

source common-setup.sh
# popper reset

init_test
popper init myp
set +e
echo -e "yes" | popper reset
cat .popper.yml | grep 'myp'
if [ $? -eq 0 ];
then
  exit 1
fi

init_test
popper init myp
echo -e "no" | popper reset
set -e
cat .popper.yml | grep 'myp'
