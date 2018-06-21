#!/bin/bash
set -ex

source common-setup.sh

# workflow
init_test
popper init pipeone
popper workflow pipeone > wf.dot
cat wf.dot | grep digraph
cat wf.dot | grep setup
cat wf.dot | grep post_run
cat wf.dot | grep validate
cat wf.dot | grep teardown

