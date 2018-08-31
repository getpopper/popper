#!/bin/bash
set -ex

source common-setup.sh

init_test

popper init mypipe --stages=one,two

popper parameters mypipe --add key1=val1 --add key2=val2
popper parameters mypipe --add key2=new_val_2 --add key3=val3

popper env mypipe --add alpine-3.4

popper run

test -f pipelines/mypipe/popper/host/0/one.sh.out
test -f pipelines/mypipe/popper/host/1/one.sh.out
test -f pipelines/mypipe/popper/alpine-3.4/0/one.sh.out
test -f pipelines/mypipe/popper/alpine-3.4/1/one.sh.out
test -f pipelines/mypipe/popper/host/0/one.sh.err
test -f pipelines/mypipe/popper/host/1/one.sh.err
test -f pipelines/mypipe/popper/alpine-3.4/0/one.sh.err
test -f pipelines/mypipe/popper/alpine-3.4/1/one.sh.err
