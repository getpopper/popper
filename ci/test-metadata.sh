#!/bin/bash
set -ex

source common-setup.sh

init_test

# metadata
popper metadata --add authors='the ramones, sex pistols'
popper metadata | grep 'the ramones, sex pistols'
popper metadata --add authors='the police'
popper metadata | grep 'the police'
popper metadata --add year=1979
popper metadata | grep "year"
popper metadata | grep "the police"


