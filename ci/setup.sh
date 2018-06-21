#!/bin/bash
set -ex

if USE_VIRTUALENV
then
  echo "Creating temporary virtualenv"
  virtualenv /tmp/popper-env
  source /tmp/popper-env/bin/activate

  cd ../cli

  pip install .
fi


