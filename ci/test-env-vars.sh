#!/bin/bash
set -ex

source common-setup.sh

#env-vars
init_test

popper init mypipeone

popper env-vars mypipeone --add key1=val1 --add key2=val2
popper env-vars mypipeone | grep -q key1
popper env-vars mypipeone | grep -q key2

set +e
popper env-vars mypipeone --rm key1=val1
if [ $? -eq 0 };
then
  exit 1
fi
set -e

popper env-vars mypipeone --rm key1=val1 --rm key2=val2
! popper env-vars mypipeone | grep -q key1
! popper env-vars mypipeone | grep -q key2

init_test
popper init mypipeone

set +e
popper env-vars --add key1=val1
if [ $? -eq 0 ];
then
    exit 1
fi
set -e

cd pipelines/mypipeone
popper env-vars --add key1=val1
