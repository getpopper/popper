#!/bin/bash
set -ex

if [[ -n $WITH_K8S ]]; then
  git clone \
    --depth 1 \
    --branch "v0.7.0-2" \
    --single-branch \
    https://github.com/k8s-school/kind-travis-ci.git

  ./kind-travis-ci/kind/k8s-create.sh

  mkdir -p $HOME/.kube

  cp $(kind get kubeconfig-path --name="kind") $HOME/.kube/config  
fi