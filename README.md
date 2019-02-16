# <img src="https://raw.githubusercontent.com/systemslab/popper/57f7a89bed6ff3e4d62ea2a5683ae28e3251931e/docs/figures/popper_logo_just_jug.png" width="64" valign="middle" alt="Popper"/> Popper

[![Downloads](https://pepy.tech/badge/popper)](https://pepy.tech/project/popper)
[![Build Status](https://travis-ci.org/systemslab/popper.svg?branch=master)](https://travis-ci.org/systemslab/popper)
[![Join the chat at https://gitter.im/systemslab/popper](https://badges.gitter.im/systemslab/popper.svg)](https://gitter.im/falsifiable-us/popper?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)
[![PyPI version](https://badge.fury.io/py/popper.svg)](https://badge.fury.io/py/popper)
[![GitHub license](https://img.shields.io/github/license/systemslab/popper.svg)](https://github.com/systemslab/popper/blob/master/LICENSE)
[![Popper Status](http://badges.falsifiable.us/systemslab/popper)](http://popper.rtfd.io/en/latest/sections/badge_server.html) 

Popper is a workflow execution engine based on [Github 
actions](https://github.com/features/actions) (GHA). Popper workflows 
are defined in a [HCL](https://github.com/hashicorp/hcl) syntax and 
behave like GHA workflows. The main difference is that a Popper 
workflow can execute actions in other runtimes besides Docker. The 
workflow language is strictly a superset of GHA's workflow language so 
Popper can run a GHA workflow locally.

In addition to running a workflow, the Popper CLI tool provides other 
useful functionality:

  * Search
  * Continuous integration
  * Action scaffolding

As part of this effort, we also maintain a repository of Popper 
[actions](https://github.com/popperized/library).

This repository contains:

  * A [CLI tool](popper/) to run and implement popper workflows.
  * [Documentation](http://popper.readthedocs.io/en/latest/) about the
    convention and the CLI tool.
  * Contents of our [landing page](http://falsifiable.us) ([`gh-pages`](https://github.com/systemslab/popper/tree/gh-pages) branch).

Quick links to other resources:

  * [5-minute screencast demo of the CLI](https://asciinema.org/a/227046).
  * [Slidedeck introducing the convention](https://www.slideshare.net/ivotron/the-popper-experimentation-protocol-and-cli-tool-86987253).
  * [Recorded webinar presentation](https://youtu.be/tZcaV31FxUM).
  * [Software Carpentry formatted Lesson](https://popperized.github.io/swc-lesson/).
  * [List of repositories that follow the convention](https://github.com/popperized).

## Installation

See [here](cli/) for instructions on how to install the CLI tool. Once
installed, to get an overview and list of commands check out the
command line help:

```bash
popper --help
```

For a quickstart guide on how to use the CLI, look [here](https://popper.readthedocs.io/en/v1.1.2/sections/getting_started.html).


## Contributing

Anyone is welcome to contribute to Popper! To get started, take a look
at our [contributing guidelines](CONTRIBUTING.md), then dive in with our [list of good first issues](https://github.com/systemslab/popper/issues?utf8=%E2%9C%93&q=is%3Aissue+label%3A%22good+first+issue%22+is%3Aopen)
and [open projects](https://github.com/systemslab/popper/projects).


## Participation Guidelines

Popper adheres to the code of conduct [posted in this repository](CODE_OF_CONDUCT.md). By participating or contributing to Popper, you're expected to uphold this code. If you encounter unacceptable behavior, please immediately [email us](mailto:ivo@cs.ucsc.edu).
