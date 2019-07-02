#!/bin/bash
set -ex

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