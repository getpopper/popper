#!/bin/bash
set -ex

if [[ $ENGINE == "singularity" ]]; then
  sudo add-apt-repository 'deb http://ftp.de.debian.org/debian bullseye main'
  sudo apt-get update
  wget http://ftp.us.debian.org/debian/pool/main/s/singularity-container/singularity-container_3.5.2+ds1-1_amd64.deb
  sudo apt-get -f --allow-unauthenticated -y install ./singularity-container_3.5.2+ds1-1_amd64.deb
  singularity version
fi

if [[ -n $WITH_K8S ]]; then
  git clone \
    --depth 1 \
    --branch "v0.7.0-2" \
    --single-branch \
    https://github.com/k8s-school/kind-travis-ci.git

  ./kind-travis-ci/kind/k8s-create.sh
fi
