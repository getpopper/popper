#!/bin/bash
set -ex

source common-setup.sh

# test popper rm command
init_test
popper init mypipetwo
popper rm mypipetwo

# test popper rm with paper
popper init paper
popper rm paper