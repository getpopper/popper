#!/bin/bash
set -ex

source common-setup.sh

# env
init_test
popper init mypipeone
popper env mypipeone | grep 'host'
popper env mypipeone --add foo
popper env mypipeone | grep 'host'
popper env mypipeone | grep 'foo'
popper env mypipeone --add bar,baz
popper env mypipeone | grep 'host'
popper env mypipeone | grep 'foo'
popper env mypipeone | grep 'bar'
popper env mypipeone | grep 'baz'
popper env mypipeone --rm foo,bar,baz
popper env mypipeone | grep 'host'

# test listing of available environments
popper env --ls


