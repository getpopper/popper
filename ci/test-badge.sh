#!/bin/bash
set -ex

source common-setup.sh

popper badge cloudlab | grep "\[\!\[.*\](.*)\](.*)"

set +e
popper badge
if [ $? -eq 0 ];
then
  exit 1
fi

popper badge errorout

if [ $? -eq 0 ];
then
  exit 1
fi

set -e

popper badge popper | grep 'http://badges.falsifiable.us/systemslab/popper'
popper badge popper | grep 'http://popper.rtfd.io/en/latest/sections/badge_server.html'
