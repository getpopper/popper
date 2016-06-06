#!/bin/bash
set -e

# TODO add flags:
#   - help: show quick help message
#   - empty: don't generate content in files, just their names and a comment

echo "Initializing a Popper repository"
git init

mkdir experiments
mkdir paper

# TODO add variables holding file contents (or find other way to do it)

echo $paper.tex > paper/paper.tex

