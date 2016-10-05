#!/bin/bash
set -e -x
docker run -d -v `pwd`:/home/jovyan/work -p 8888:8888 jupyter/scipy-notebook
echo "Open Browser and point it to http://localhost:8888"
