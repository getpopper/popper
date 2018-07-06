#!/bin/bash
set -ex

function init_test {
  cd
  rm -rf /tmp/mypaper
  mkdir /tmp/mypaper
  cd /tmp/mypaper
  git init
  git remote add origin https://github.com/systemslab/popper.git
  popper init
}

if [ $USE_VIRTUALENV ];
then
  source /tmp/popper-env/bin/activate
fi

which popper

