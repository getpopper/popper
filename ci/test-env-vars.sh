#!/bin/bash
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
