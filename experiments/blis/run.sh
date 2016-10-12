#!/bin/bash
set -e -x
docker pull ivotron/blis
docker run --rm -v `pwd`/results:/blis/test/output ivotron/blis
