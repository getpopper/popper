#!/bin/bash

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

which popper

