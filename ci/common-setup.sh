#!/bin/bash

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

if [ -f /.dockerenv ]; then
  output_dir=popper
else
  output_dir=popper/host
fi

pipe_ran() {
  test -d $repo_root/pipelines/$1/$output_dir
}

pipe_didnt_run() {
  test ! -d $repo_root/pipelines/$1/$output_dir
}

stage_ran() {
  test -f $repo_root/pipelines/$1/$output_dir/$2.sh.out
  test -f $repo_root/pipelines/$1/$output_dir/$2.sh.err
}

stage_didnt_run() {
  test ! -f $repo_root/pipelines/$1/$output_dir/$2.sh.out
  test ! -f $repo_root/pipelines/$1/$output_dir/$2.sh.err
}

if [ $USE_VIRTUALENV ];
then
  source /tmp/popper-env/bin/activate
fi

export PATH=$PATH:$PWD/cli/bin
export PYTHONUNBUFFERED=1

echo Testing with popper binary located at $( which popper )

