#!/bin/bash
set -ex

source common-setup.sh

init_test
git remote add origin git@github.com/foo/bar
popper badge --service cloudlab | grep "\[\!\[.*\](.*)\](.*)"

! popper badge
! popper badge --service errorout

popper badge --service popper

popper badge --history > /tmp/history.log

init_test
git remote add origin git@github.com/foo/bar
touch README.md
popper badge --service gce --inplace
cat README.md | grep 'https://img.shields.io/badge/GCE-ready-blue.svg'
