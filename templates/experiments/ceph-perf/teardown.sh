#!/bin/bash
# Put all your cleanup tasks here.
set -e

ARGS="--forks 50 --skip-tags package-install,with_pkg"
VARS="-e @/popper/vars.yml -e @/popper/ansible/vars.yml -i /etc/ansible/hosts"
docker run -it --rm \
  --net host \
  -v $HOME/.ssh:/root/.ssh \
  -v `pwd`:/popper \
  -v `pwd`/ansible/roles/ceph:/root -w /root \
  -v `pwd`/ansible/roles/ceph/group_vars/:/root/group_vars \
  -v `pwd`/hosts:/etc/ansible/hosts \
  -v `pwd`/ansible/ansible.cfg:/etc/ansible/ansible.cfg \
  -v `pwd`/ansible/ceph.yml:/root/ceph.yml \
  -e ANSIBLE_CONFIG="/etc/ansible/ansible.cfg" \
  michaelsevilla/ansible $ARGS $VARS /popper/ansible/cleanup.yml
  #--entrypoint=/bin/bash michaelsevilla/ansible -c "$@"
 
exit 0
