#!/bin/bash
set -ex

if [ -z "$MACHINE" ]; then
  echo "Expecting MACHINE environment variable"
  exit 1
fi
if [ -z "$USERNAME" ]; then
  echo "Expecting USERNAME environment variable"
  exit 1
fi

scp -r ./ $USERNAME@$MACHINE:

ssh $USERNAME@$MACHINE sbatch job.sh
