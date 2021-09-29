#!/bin/bash
set -ex

if [[ -z $ENABLE_TASK_TRANSLATOR_TESTS ]]; then
  exit 0
fi

# install task
sudo sh -c "$(curl --location https://taskfile.dev/install.sh)" -- -d -b /usr/local/bin
