#!/bin/bash
set -ex

source common-setup.sh

init_test

popper init mypipeone

popper parameters mypipeone --add key1=val1 --add key2=val2
popper parameters mypipeone | grep -q key1: val1
popper parameters mypipeone | grep -q key2: val2

set +e
popper parameters mypipeone --rm key1=val1
if [ $? -eq 0 };
then
  exit 1
fi
set -e

popper parameters mypipeone --rm key1=val1 --rm key2=val2
! popper parameters mypipeone | grep -q key1
! popper parameters mypipeone | grep -q key2

init_test
popper init mypipeone

set +e
popper parameters --add key1=val1
if [ $? -eq 0 ];
then
    exit 1
fi
set -e

cd pipelines/mypipeone
popper parameters --add key1=val1
