#!/bin/bash
set -ex

# test popper version command

cd ../cli
POPPER_VERSION=$(popper version)
SDIST_VER=$(python setup.py --version)
SDIST_VER="popper version $SDIST_VER"

if [ "$POPPER_VERSION" != "$SDIST_VER" ]; then
    exit 1
fi
