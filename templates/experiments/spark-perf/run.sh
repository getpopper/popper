#!/bin/bash
set -e -x

# delete previous results
sudo rm -f results/runtime_*
sudo rm -fr results/machine/*

docker run --rm -ti \
  -v `pwd`/ansible:/experiment \
  -v `pwd`/../../vendor/baseliner:/experiment/roles/baseliner \
  -v `pwd`/results:/results \
  -v $HOME/.ssh/issdm_rsa:/root/.ssh/id_rsa \
  --workdir=/experiment \
  --net=host \
  --entrypoint=/bin/bash \
  ivotron/ansible:2.2.0.0 -c \
    "ansible-playbook -e results_path=/results/output -e @vars.yml playbook.yml"
