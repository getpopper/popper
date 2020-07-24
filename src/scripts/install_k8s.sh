#!/bin/bash
set -ex

if [[ -n "$WITH_K8S" ]]; then
  # download kind
  curl -Lo ./kind "https://kind.sigs.k8s.io/dl/v0.8.1/kind-$(uname)-amd64"
  chmod +x ./kind
  mv ./kind /some-dir-in-your-PATH/kind

  # create cluster
  kind create cluster
fi