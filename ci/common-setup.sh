#!/bin/bash
set -ex

function init_test {
  cd
  rm -rf /tmp/mypaper
  mkdir /tmp/mypaper
  cd /tmp/mypaper
  git init
  popper init
}

if [ $USE_VIRTUALENV ];
then
  source /tmp/popper-env/bin/activate
fi

export PATH=$PATH:$PWD/cli/bin
export PYTHONUNBUFFERED=1

which popper

