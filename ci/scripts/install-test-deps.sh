#!/bin/bash
set -ex

if [[ $ENGINE == "singularity" ]]; then
  sudo apt-get update
  sudo apt-get install -y build-essential libssl-dev uuid-dev libgpgme11-dev libseccomp-dev pkg-config squashfs-tools
  mkdir -p ${GOPATH}/src/github.com/sylabs
  cd ${GOPATH}/src/github.com/sylabs
  git clone https://github.com/sylabs/singularity.git
  cd singularity
  git checkout v3.2.0
  cd ${GOPATH}/src/github.com/sylabs/singularity
  ./mconfig
  cd ./builddir
  make
  sudo make install
  singularity version
  cd $TRAVIS_BUILD_DIR
fi

if [[ $RESMAN == "kubernetes" ]]; then
  git clone --depth 1 -b "v0.7.0-2" --single-branch https://github.com/k8s-school/kind-travis-ci.git
  ./kind-travis-ci/kind/k8s-create.sh
  rm -r $HOME/.kube
  mkdir $HOME/.kube
  cp $(kind get kubeconfig-path) $HOME/.kube/config
fi
