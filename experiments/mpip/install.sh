#!/bin/bash

# installs dependencies of the experiment using Spack

export SPACK_ROOT=/path/to/spack
source $SPACK_ROOT/share/spack/setup-env.sh
export PATH=$SPACK_ROOT/bin:$PATH

# TODO install architecture-specific versions

spack install lulesh+mpip
