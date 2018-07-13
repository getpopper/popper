#!/bin/bash
set -ex

function init_test {
  cd
  sudo rm -rf /tmp/mypaper
  sudo mkdir /tmp/mypaper
  cd /tmp/mypaper
  git init
  popper init
}

if [ $USE_VIRTUALENV ];
then
  source /tmp/popper-env/bin/activate
fi

which popper

