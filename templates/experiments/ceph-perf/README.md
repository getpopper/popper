# ceph-perf

Ceph is a distributed object store that stores data by striping and replicating
data across a reliable object store, called RADOS. In order to properly
evaluate systems built on Ceph (e.g., Mantle, Malacology, ZLog, and CudeleFS),
we must first sanity check our cluster. This Popper template has code for
deploying, measuring, and analyzing a Ceph cluster on multiple nodes. It can
also run on a single node but the results are not as meaningful since all Ceph
processes will be co-located, fighting for resources.

## Configuration

`hosts` and `vars.yml` should be edited for your cluster configuration. For
tuning Ceph, change [ceph.conf](ansible/group_vars/all) and to change the
Ansible Ceph settings, change the [group variables](ansible/group_vars).

## Quickstart

The simplest use case is:

```
$ ./setup.sh
$ docker push <my new image>
$ ./run.sh
$ visualize/jupyter.sh
```

This templates uses Docker to build the images and Ansible to deploy Ceph and
run experiments. Between running [`setup.sh`](setup.sh) and [`run.sh`](run.sh),
the user should push the Docker image to a Docker registry (in our example, we
push to our personal DockerHub account). After `run.sh` completes, users can
run the notebook in [`visualize/`][visualize/viz.ipynb] using the Jupyter script.

EOF
