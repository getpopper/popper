#!/bin/sh
set -e

if [ -z "`which docker`" ]; then
    echo "Could not find docker." >&2
    echo "Please use the following script to install it: https://get.docker.com/." >&2
    exit 1
fi

docker run --rm -v `pwd`/popper:/app -w /app treeder/go vendor
docker run --rm -v `pwd`/popper:/app -w /app treeder/go build

echo "Success. Popper is available at 'popper/app'."
echo "Note that the executable requires libc-musl: https://www.musl-libc.org/."
