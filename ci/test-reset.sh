#!/bin/bash
set -ex

source common-setup.sh

# reset removes files and modifies .popper.yml
init_test
popper init myp
set +e
echo -e "yes" | popper reset
cat .popper.yml | grep 'myp'
if [ $? -eq 0 ];
then
  exit 1
fi

# if user selects 'n', we should not do anything
init_test
popper init myp
printf 'n' | popper reset
set -e
cat .popper.yml | grep 'myp'

# untracked files should be left intact
touch pipelines/myp/untracked
echo -e "yes" | popper reset
test -f pipelines/myp/untracked
