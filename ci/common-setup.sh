#!/bin/bash
set -ex

function init_test {
  cd
  set +e
  if ! rm -rf /tmp/mypaper; then
    # try to remove using docker
    docker run --rm -v /tmp:/tmp alpine:3.8 rm -rf /tmp/mypaper
  fi
  set -e
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

