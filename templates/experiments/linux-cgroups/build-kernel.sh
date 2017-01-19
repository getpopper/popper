#!/bin/bash
set -e -x

# build deb packages
rm -f vagrant/debs/*
docker build -t kernel-ci docker/
docker run --rm -ti \
  -e CHECK_KEY=false \
  -v `pwd`/docker/linux:/linux \
  -v `pwd`/patches:/app/patches \
  kernel-ci
cp docker/linux/*.deb vagrant/debs/


