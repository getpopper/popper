#!/bin/sh
set -e

if [ -z "`which docker`" ]; then
    echo "Could not find docker." >&2
    echo "Please use the following script to install it: https://get.docker.com/." >&2
    exit 1
fi

docker build -t falsifiable/popper popper/

echo "Success. Popper is available at 'falsifiable/popper'."
