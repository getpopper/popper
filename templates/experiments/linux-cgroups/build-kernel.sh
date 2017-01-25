#!/bin/bash
set -e -x

# build deb packages
rm -f vagrant/debs/*
docker build -t kernel-ci docker/
docker run --rm -ti -v `pwd`/linux:/linux kernel-ci
mv linux/*.deb vagrant/debs/
