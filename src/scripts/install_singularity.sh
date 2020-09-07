#!/bin/bash
set -ex

if [[ $ENGINE != "singularity" ]]; then
  exit 0
fi

sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 648ACFD622F3D138
sudo add-apt-repository "deb http://ftp.de.debian.org/debian sid main"
sudo apt install -y singularity-container
singularity version
