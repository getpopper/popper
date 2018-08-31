#!/bin/bash
set -ex

source common-setup.sh

sleep 10

# test popper search command
init_test
popper search quiho
popper search --include-readme 'linux kernel vagrant' | grep 'examples/vagrant-linux'
test -d ./.pipeline_cache.yml

popper search --ls
popper search --skip-update quiho
popper search --skip-update linux
popper search --rm popperized

set +e
cat .popper.yml | grep '- popperized'
if [ $? -eq 0 ]; then
  exit 1
fi
set -e

popper search --add popperized
cat .popper.yml | grep '- popperized'
init_test

set +e
popper search --skip-update quiho
if [ $? -eq 0 ];
then
  exit 1
fi
set -e

popper info popperized/popper-readthedocs-examples/vagrant-linux | grep 'exemplifies the use of Popper'
