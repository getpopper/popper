#!/bin/bash
set -e -x

docker run --rm -ti \
  -v `pwd`:/experiment \
  -v "$SSH_AUTH_SOCK:/tmp/ssh_auth_sock" \
  -e "SSH_AUTH_SOCK=/tmp/ssh_auth_sock" \
  --workdir=/experiment \
  --net=host \
  --entrypoint=/experiment/.entrypoint.sh \
  williamyeh/ansible:debian8

