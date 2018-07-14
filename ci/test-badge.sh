#!/bin/bash
set -ex

source common-setup.sh

popper badge --service cloudlab | grep "\[\!\[.*\](.*)\](.*)"

set +e
popper badge
if [ $? -eq 0 ];
then
  exit 1
fi

popper badge --service errorout

if [ $? -eq 0 ];
then
  exit 1
fi

set -e

popper badge --service popper | grep 'http://badges.falsifiable.us/systemslab/popper'
popper badge --service popper | grep 'http://popper.rtfd.io/en/latest/sections/badge_server.html'

popper badge --history

init_test
touch README.md
popper badge --service gce --inplace
