#!/usr/bin/env bash
# [wf] execute run stage
set -ex

docker run --rm -e CI=1 -e POPPER_FIGSHARE_API_TOKEN="${POPPER_FIGSHARE_API_TOKEN}" \
    -e POPPER_ZENODO_API_TOKEN="${POPPER_ZENODO_API_TOKEN}" \
    -e POPPER_GITHUB_API_TOKEN="${POPPER_GITHUB_API_TOKEN}" \
    --workdir=/tests \
    -v `pwd`/../../:/tests falsifiable/popper \
    run run-tests
