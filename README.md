# <img src="https://raw.githubusercontent.com/systemslab/popper/57f7a89bed6ff3e4d62ea2a5683ae28e3251931e/docs/figures/popper_logo_just_jug.png" width="64" valign="middle" alt="Popper"/> Popper

[![Downloads](https://pepy.tech/badge/popper)](https://pepy.tech/project/popper)
[![Build Status](https://travis-ci.org/systemslab/popper.svg?branch=master)](https://travis-ci.org/systemslab/popper)
[![Join the chat at https://gitter.im/systemslab/popper](https://badges.gitter.im/systemslab/popper.svg)](https://gitter.im/falsifiable-us/popper?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)
[![PyPI version](https://badge.fury.io/py/popper.svg)](https://badge.fury.io/py/popper)
[![GitHub license](https://img.shields.io/github/license/systemslab/popper.svg)](https://github.com/systemslab/popper/blob/master/LICENSE)

> **NOTE**: Popper 2.0 is a revamped version of the Popper project. 
> For 1.x releases, go to the [`v1.x` 
> branch](https://github.com/systemslab/popper/tree/v1.x).

Popper is a workflow execution engine based on [Github 
actions](https://github.com/features/actions) (GHA). Popper workflows 
are defined in [HCL](https://github.com/hashicorp/hcl) syntax and 
behave like GHA workflows. The main difference with respect to GHA 
workflows is that a Popper workflow can execute actions in other 
runtimes in addition to Docker. The workflow language is strictly a 
superset of GHA workflow language so Popper can run a GHA workflow 
locally as if it was being executed by the GHA platform.

In addition to running a GHA workflow locally, Popper provides other 
useful functionality:

  * [Other runtimes](). Actions can execute locally on the host where 
    a `popper` command runs (i.e. "outside" a container, thus not 
    depending on Docker). We are working in adding support for other 
    runtimes are such as [`rkt`](https://github.com/rkt/rkt), 
    [Vagrant](https://www.vagrantup.com/), 
    [Singularity](https://sylabs.io/) and others (see [this project]() 
    for more).
  * [Search](). Allows users to browse through a catalog of available 
    actions.
  * [Continuous integration](). Generate configuration files for 
    distinct CI services that allow workflows to run on these (Travis, 
    Jenkins, Gitlab and Circle supported).
  * [Action scaffolding]() **(Coming Soon)**. Aid in the 
    implementation of new actions or building upon existing ones.

As part of this effort, we also maintain a repository of 
[actions](https://github.com/popperized/library). The contents of this 
repository are:

  * [`cli/`](cli/). The codebase of the CLI tool.
  * [`docs/`](docs/). General 
    [documentation](http://popper.readthedocs.io/en/latest/) 
    containing guides, CLI documentation and pointers to other 
    resources.
  * [`gh-pages`](https://github.com/systemslab/popper/tree/gh-pages) 
    branch. Contents of our [landing page](http://falsifiable.us).

Quick links to other resources:

  * [5-minute screencast demo of the CLI](https://asciinema.org/a/227046).
  * [Recorded webinar presentation](https://youtu.be/tZcaV31FxUM).
  * [Software Carpentry formatted Lesson](https://popperized.github.io/swc-lesson/).
  * [List of repositories that implement Popper 
    workflows](https://github.com/popperized).

## Installation

See [here](cli/) for instructions on how to install the CLI tool. Once
installed, to get an overview and list of commands check out the
command line help:

```bash
popper --help
```

For a quickstart guide on how to use the CLI, look 
[here](https://popper.readthedocs.io/en/latest/sections/getting_started.html).

## Contributing

Anyone is welcome to contribute to Popper! To get started, take a look
at our [contributing guidelines](CONTRIBUTING.md), then dive in with our [list of good first issues](https://github.com/systemslab/popper/issues?utf8=%E2%9C%93&q=is%3Aissue+label%3A%22good+first+issue%22+is%3Aopen)
and [open projects](https://github.com/systemslab/popper/projects).

## Participation Guidelines

Popper adheres to the code of conduct [posted in this repository](CODE_OF_CONDUCT.md). By participating or contributing to Popper, you're expected to uphold this code. If you encounter unacceptable behavior, please immediately [email us](mailto:ivo@cs.ucsc.edu).
