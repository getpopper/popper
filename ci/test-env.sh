#!/bin/bash
set -ex

source common-setup.sh

# env
init_test
popper init mypipeone
popper env mypipeone | grep '[host]'
popper env mypipeone --add foo
popper env mypipeone | grep 'host'
popper env mypipeone | grep 'foo'
popper env mypipeone --add bar,baz
popper env mypipeone | grep 'host'
popper env mypipeone | grep 'foo'
popper env mypipeone | grep 'bar'
popper env mypipeone | grep 'baz'
popper env mypipeone --rm foo,bar,baz
popper env mypipeone | grep '[host]'

# test listing of available environments
popper env --ls

set +e
popper env
if [ $? -eq 0 ]; then
    exit 1
fi
set -e
cd pipelines/mypipeone
popper env

# test running inside containers
init_test

popper init mypipe --stages=one,two
popper env mypipe --add alpine-3.4
popper env mypipe --rm host
popper run

test -f pipelines/mypipe/popper/alpine-3.4/one.sh.err
test -f pipelines/mypipe/popper/alpine-3.4/one.sh.out
test -f pipelines/mypipe/popper/alpine-3.4/two.sh.err
test -f pipelines/mypipe/popper/alpine-3.4/two.sh.out

init_test

popper init mypipe --stages=one,two
popper env mypipe --add alpine-3.4
popper env mypipe --add debian-9
popper run

test -f pipelines/mypipe/popper/alpine-3.4/one.sh.err
test -f pipelines/mypipe/popper/alpine-3.4/one.sh.out
test -f pipelines/mypipe/popper/alpine-3.4/two.sh.err
test -f pipelines/mypipe/popper/alpine-3.4/two.sh.out
test -f pipelines/mypipe/popper/debian-9/one.sh.err
test -f pipelines/mypipe/popper/debian-9/one.sh.out
test -f pipelines/mypipe/popper/debian-9/two.sh.err
test -f pipelines/mypipe/popper/debian-9/two.sh.out
test -f pipelines/mypipe/popper/host/one.sh.err
test -f pipelines/mypipe/popper/host/one.sh.out
test -f pipelines/mypipe/popper/host/two.sh.err
test -f pipelines/mypipe/popper/host/two.sh.out

# test running user-defined container images
init_test

popper init mypipe --stages=one
popper env mypipe --add user/img-with-popper-inside:alpine-3.4
popper env mypipe --rm host

popper run

test -f "pipelines/mypipe/popper/user_img-with-popper-inside:alpine-3.4/one.sh.err"
test -f "pipelines/mypipe/popper/user_img-with-popper-inside:alpine-3.4/one.sh.out"

init_test

popper init mypipe --stages=one,two
popper env mypipe --add alpine-3.4 --args --runtime=runc
popper env mypipe --add alpine-3.4 --args --runtime=runc,--ipc=host

popper env mypipe | grep 'runtime=runc'
popper env mypipe | grep 'ipc=host'

popper run

