#!/bin/bash
set -ex

repo_root=/tmp/mypaper

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

echo Testing with popper command located at $( which popper )
