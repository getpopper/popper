#!/bin/bash
set -ex

source common-setup.sh

# when pipelines are present
init_test
popper init experiment1
popper ls | grep 'experiment1'

# when no pipelines are present
init_test
popper ls | grep 'There are no pipelines in this repository'
