# <img src="https://raw.githubusercontent.com/systemslab/popper/57f7a89bed6ff3e4d62ea2a5683ae28e3251931e/docs/figures/popper_logo_just_jug.png" width="64" valign="middle" alt="Popper"/> Popper

[![Downloads](https://pepy.tech/badge/popper/month)](https://pepy.tech/project/popper)
[![Build Status](https://travis-ci.org/systemslab/popper.svg?branch=master)](https://travis-ci.org/systemslab/popper)
[![codecov](https://codecov.io/gh/systemslab/popper/branch/master/graph/badge.svg)](https://codecov.io/gh/systemslab/popper)
[![Join the chat at https://gitter.im/systemslab/popper](https://badges.gitter.im/systemslab/popper.svg)](https://gitter.im/falsifiable-us/popper?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)
[![PyPI version](https://badge.fury.io/py/popper.svg)](https://badge.fury.io/py/popper)
[![GitHub license](https://img.shields.io/github/license/systemslab/popper.svg)](https://github.com/systemslab/popper/blob/master/LICENSE)

<p align="center">
  <img src="docs/figures/demo.gif" width="800">
</p>

Popper is a tool for defining and executing [container-native][cn] 
workflows. With Popper, you define a workflow in a YAML file, and then 
execute it with a single command. The goal of this project is to 
provide the following:

  * **Lightweight workflow definition syntax.** Defining a workflow is 
  as simple as writing file in a [lightweight YAML syntax][cnwf] and 
  invoking `popper run` (see demo above). If you're familiar with 
  [Docker Compose][compose], you can think of Popper as Compose but 
  for workflows instead of services.
  * **Abstract container runtimes**. In addition to Docker, Popper can 
  execute workflows in other runtimes by interacting with distinct 
  container engines. We currently support [Singularity][sylabs], as 
  well as running Docker inside virtual machines (via 
  [Vagrant][vagrant]). We are working on adding 
  [Podman](https://podman.io) to the list.
  * **Continuous integration**. Generate configuration files for 
  distinct CI services, allowing users to seamlessly execute workflows 
  on Travis, Jenkins, Gitlab, Circle and others.
  * **Workflow development**. Aid in the implementation and debugging 
  of [workflows][scaffold], and provide with an extensive list of 
  [example workflows](https://github.com/popperized) that can serve as 
  a starting point.

-----

This repository contains:

  * [`cli/`](cli/). The codebase of the command-line tool.
  * [`docs/`](docs/). General [documentation][docs] containing guides, 
    CLI documentation and pointers to other resources.
  * [`gh-pages`][gh-pages] branch. Contents of our [landing 
    page](http://falsifiable.us).

## Installation

To run workflows, you need to have Python 3.6+, Git and a container 
engine installed ([Docker][docker], [Singularity][singularity] and 
[Vagrant](https://vagrantup.com/) are currently supported). To install 
Popper you can use [`pip`](https://pypi.python.org/pypi). We recommend 
to install in a virtual environment (see [here][venv] for more on 
`virtualenv`). To install:

```bash
pip install popper
```

Once installed, you can get an overview and list of available 
commands:

```bash
popper --help
```

For a Quickstart guide on how to use Popper, look [here][getting_started].

## Contributing

Anyone is welcome to contribute to Popper! To get started, take a look 
at our [contributing guidelines](CONTRIBUTING.md), then dive in with 
our [list of good first issues][gfi].

## Participation Guidelines

Popper adheres to the code of conduct [posted in this 
repository](CODE_OF_CONDUCT.md). By participating or contributing to 
Popper, you're expected to uphold this code. If you encounter 
unacceptable behavior, please immediately [email 
us](mailto:ivo@cs.ucsc.edu).

[gfi]: https://github.com/systemslab/popper/issues?utf8=%E2%9C%93&q=is%3Aissue+label%3A%22good+first+issue%22+is%3Aopen
[singularity]: https://github.com/sylabs/singularity
[docker]: https://get.docker.com
[getting_started]: https://popper.readthedocs.io/en/latest/sections/getting_started.html
[venv]: https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/#installing-virtualenv
[popper2]: https://github.com/systemslab/popper/projects/12
[docs]: https://popper.readthedocs.io/en/latest/
[gh-pages]: https://github.com/systemslab/popper/tree/gh-pages
[scaffold]: https://popper.readthedocs.io/en/latest/sections/getting_started.html#create-a-workflow
[cnwf]: docs/sections/cn_workflows.md
[sylabs]: https://sylabs.io/
[vagrant]: https://vagrantup.com/
[cn]: https://cloudblogs.microsoft.com/opensource/2018/04/23/5-reasons-you-should-be-doing-container-native-development/
[compose]: https://docs.docker.com/compose/
