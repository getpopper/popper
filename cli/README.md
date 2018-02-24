# Popper-CLI

A CLI tool to help bootstrap projects that follow the 
[Popper](https://github.com/systemslab/popper) convention.

## Install

### `pip`

We have a [`pip`](https://pypi.python.org/pypi) package available. To 
install:

```bash
pip install popper
```

### Manual

```bash
git clone --recursive git@github.com:systemslab/popper
export PATH=$PATH:$PWD/popper/cli/bin
```

> **NOTE**: the `--recursive` flag is needed in order to checkout all 
the dependencies.

## Usage

To get an overview and list of commands check out the command line 
help:

```bash
popper --help
```
