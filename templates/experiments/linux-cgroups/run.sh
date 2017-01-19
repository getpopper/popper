#!/bin/bash
set -e -x

# build deb packages
./build-kernel.sh

# provision new kernel and start VM
(cd vagrant && ./provision.sh)

# run test
(cd vagrant && vagrant ssh -c './run_test')
