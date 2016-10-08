#!/bin/bash

source ./.common.sh
find_or_install_spack

# installs dependencies of the experiment using Spack
# TODO install architecture-specific versions

spack install openmpi@2.0.1
spack install lulesh+mpip
