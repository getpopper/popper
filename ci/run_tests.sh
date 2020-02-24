#!/bin/bash
set -e

if [ -z "$ENGINE" ]; then
  echo "Expecting ENGINE variable"
  exit 1
fi

echo "###################################"
echo "actions-demo"
ci/test/actions-demo
echo "###################################"
echo "reuse"
#ci/test/reuse
echo "###################################"
ci/test/validate
echo "###################################"
ci/test/scaffold
echo "###################################"
ci/test/dry-run
echo "###################################"
# ci/test/parallel
echo "###################################"
ci/test/dot
echo "###################################"
# ci/test/interrupt
echo "###################################"
ci/test/quiet
echo "###################################"
ci/test/sh
echo "###################################"
ci/test/skip
echo "###################################"
#ci/test/substitutions
echo "###################################"
ci/test/offline
echo "###################################"
ci/test/engine-conf
