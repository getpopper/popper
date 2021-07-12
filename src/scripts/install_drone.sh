#!/bin/bash
set -ex

if [[ -z $ENABLE_DRONE_TRANSLATOR_TESTS ]]; then
  exit 0
fi

# download drone cli
curl -L https://github.com/drone/drone-cli/releases/latest/download/drone_linux_amd64.tar.gz | tar zx
sudo mv ./drone /usr/local/bin/drone
