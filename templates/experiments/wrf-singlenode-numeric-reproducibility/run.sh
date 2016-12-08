#!/bin/bash

docker run --rm -ti \
  -v `pwd`/ansible:/experiment \
  -v `pwd`/vars.yml:/experiment/vars.yml \
  -v `pwd`/results:/results \
  -v /usr/bin/docker:/usr/bin/docker \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v $HOME/.ssh/id_rsa:/root/.ssh/id_rsa \
  -v $HOME/.ssh/id_dsa:/root/.ssh/id_dsa \
  --workdir=/experiment \
  --net=host \
  --entrypoint=/bin/bash \
  ivotron/ansible:2.2.0.0 -c \
    "ansible-playbook -e @vars.yml -e results_path=/results playbook.yml"
