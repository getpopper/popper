#!/bin/bash
sh -c "cd ansible/ && \
       ansible-playbook -e @../vars.yml -e results_path=../results playbook.yml"

# The following executes the experiment using docker (won't work on OSXs)
#
#docker run --rm -ti \
#  -v `pwd`/ansible:/experiment \
#  -v `pwd`/vars.yml:/experiment/vars.yml \
#  -v `pwd`/results:/results \
#  -v "$SSH_AUTH_SOCK:/tmp/ssh_auth_sock" \
#  -e "SSH_AUTH_SOCK=/tmp/ssh_auth_sock" \
#  --workdir=/experiment \
#  --net=host \
#  --entrypoint=/bin/bash \
#  ivotron/ansible:2.2.0.0 -c \
#    "ssh-add -l && \
#     ansible-playbook -e @vars.yml -e results_path=/results playbook.yml"
