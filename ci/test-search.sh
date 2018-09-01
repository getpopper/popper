#!/bin/bash
set -ex

source common-setup.sh

sleep 10

init_test

popper search quiho | grep 'quiho-popper/single-node'
test -f ./.pipeline_cache.yml

popper search --ls
popper search --include-readme 'kernel' | grep 'examples/vagrant-linux'
popper search --skip-update quiho | grep 'quiho-popper/single-node'
popper search --skip-update --include-readme kernel | grep 'examples/vagrant-linux'

popper search --rm popperized
! cat .popper.yml | grep '- popperized'

popper search --add popperized
cat .popper.yml | grep '- popperized'

init_test
! popper search --skip-update quiho

popper info popperized/popper-readthedocs-examples/vagrant-linux | grep 'exemplifies the use of Popper'
