#!/bin/bash
set -e -x

# delete previous results
sudo rm -rf /tmp/results/
sudo rm -rf results/

libltdl=`ldd $(which docker) | grep ltdl | sed 's/.*\( .*libltdl.so.* \).*/\1/' | sed 's/ //g'`
if [ -n "$libltdl" ] ; then
  libltdl="-v $libltdl:$libltdl"
fi

docker run --rm -ti \
  -v `pwd`/ansible:/experiment \
  -v `pwd`/../../vendor/baseliner:/experiment/roles/baseliner \
  -v /tmp:/tmp \
  -v $HOME/.ssh/issdm_rsa:/root/.ssh/id_rsa \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v /usr/bin/docker:/usr/bin/docker \
  $libltdl \
  --workdir=/experiment \
  --net=host \
  --entrypoint=/bin/bash \
  ivotron/ansible:2.2.0.0 -c \
    "ansible-playbook -e results_path=/tmp/results -e @vars.yml playbook.yml"

sudo mv /tmp/results results
