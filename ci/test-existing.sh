#!/bin/bash
set -ex

source common-setup.sh

init_test
mkdir ci
echo '' > ci/one.sh
echo '' > ci/two
echo '' > ci/three
popper init --existing --stages=one,two,three ci
cat .popper.yml | grep '\ host'
cat .popper.yml | grep '\- one'
cat .popper.yml | grep '\- two'
cat .popper.yml | grep '\- three'
cat .popper.yml | grep 'path: ci'

mkdir -p my/custom/path/to/pipeline/ci2
echo '' > my/custom/path/to/pipeline/ci2/script1.sh
echo '' > my/custom/path/to/pipeline/ci2/script2.txt
echo '' > my/custom/path/to/pipeline/ci2/script3.sh

popper init --existing --infer-stages my/custom/path/to/pipeline/ci2
cat .popper.yml| grep 'ci2:'
cat .popper.yml| grep ' - script1'
set +e
cat .popper.yml| grep ' - script2'
if [ $? -eq 0];
then
  exit 1
fi
set -e
cat .popper.yml| grep ' - script3'

set +e
popper init --existing
if [ $? -eq 0];
then
  exit 1
fi
set -e

