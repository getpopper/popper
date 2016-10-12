#!/bin/bash
set -e -x
docker run -d -v `pwd`:/code/experiment -p 8888:8888 smizy/octave:4.0.3-jupyter-alpine
echo "Open Browser and point it to http://localhost:8888/tree/experiment"
