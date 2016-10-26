#!/bin/bash
set -e -x
docker pull ivotron/blis:0.2.1-reference
docker run --rm -v `pwd`/results:/blis/test/output ivotron/blis:0.2.1-reference
