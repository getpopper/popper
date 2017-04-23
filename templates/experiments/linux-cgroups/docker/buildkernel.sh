#! /usr/bin/env bash
set -xe

# Much of this script was sourced from
# forums.debian.net/viewtopic.php?f=16&t=87006
# then *heavily* modified to support CI and Docker by https://github.com/sammcj/kernel-ci
# we then adapted it to be added as part of a Popper template

# Optional variables that may be passed to this script:

# VERSION_POSTFIX
# For restrictions see the --append-to-version option of make-kpg.c
# DEFAULT VALUE: "-ci"

# STOCK_CONFIG
# Currently using Debian Jessie backports 4.6.0 config
# DEFAULT VALUE: "config-4.6.0-0.bpo.1-amd64"
# EXAMPLE VALUE: "config-3.16.0-0.bpo.4-amd64"

# BUILD_ONLY_LOADED_MODULES
# Set to yes if you want to build only the modules that are currently
# loaded Speeds up the build. But modules that are not currently
# loaded will be missing!  Only usefull if you really have to speed up
# the build time and the kernel is intended for the running system and
# the hardware is not expected to change.
# DEFAULT VALUE: "false"

# -------------VARIABLES---------------

VERSION_POSTFIX=${VERSION_POSTFIX:-"-ci"}
BUILD_ONLY_LOADED_MODULES=${BUILD_ONLY_LOADED_MODULES:-"false"}
CONCURRENCY_LEVEL="$(grep -c '^processor' /proc/cpuinfo)"
STOCK_CONFIG=${STOCK_CONFIG:="config-4.6.0-0.bpo.1-amd64"}

# -------------PRE-FLIGHT---------------

# Check there is at least 500MB of free disk space
CheckFreeSpace() {
  if (($(df -m . | awk 'NR==2 {print $4}') < 500 )); then
    echo "Not enough free disk space, you need at least 500MB"
    exit 1
  fi
}

echo "$(getconf _NPROCESSORS_ONLN) CPU cores detected"

export BUILD_DIR="/app"
export SRC_DIR="/linux"
if [ ! -d $SRC_DIR ] ; then
  # by convention, a /linux folder is bind-mounted
  echo "couldn't find $SRC_DIR"
  exit 1
fi

mkdir -p kpatch

cd $SRC_DIR

# --------------CONFIG------------------

# Create the kernel config including patches

cp $BUILD_DIR/kernel_config.sh .

# If there is a kernel config, move it to a backup
mv -f ".config .config.old" | true

if [ -n "$CONFIG_TO_USE" ] ; then
  cp "$CONFIG_TO_USE" .config
else
  # copy config
  cp $BUILD_DIR/"$STOCK_CONFIG" .config
fi

./kernel_config.sh

# Copies the configuration of the running kernel and applies defaults to all 
# settings that are new in the upstream version.
# Use the copied configuration and apply defaults to all new settings
yes "" | make oldconfig

if [ "$BUILD_ONLY_LOADED_MODULES" = "true" ] ; then
  echo "Disabling modules that are not loaded by the running system..."
  make localmodconfig
fi

# --------------BUILD------------------

echo "Now building the kernel, this will take a while..."
time fakeroot make-kpkg --jobs "$(getconf _NPROCESSORS_ONLN)" --append-to-version "$VERSION_POSTFIX" --initrd kernel_image
time fakeroot make-kpkg --jobs "$(getconf _NPROCESSORS_ONLN)" --append-to-version "$VERSION_POSTFIX" --initrd kernel_headers

PACKAGE_NAME="$(ls -m1 /linux-image*.deb)"
HEADERS_PACKAGE_NAME="$(ls -m1 /linux-headers*.deb)"
echo "Congratulations! You just build a linux kernel."
echo "Use the following command to install it: dpkg -i $PACKAGE_NAME $HEADERS_PACKAGE_NAME"

mv /*.deb /linux/
