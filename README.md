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

Popper is a [Github Actions](https://github.com/features/actions) 
(GHA) execution engine that allows you to run GHA workflows (in [HCL 
syntax][hcl-to-yml]) locally on your machine and on CI services. The 
goal of this project is to provide the following functionality:

  * **Continuous integration**. Generate configuration files for 
    distinct CI services, allowing users to execute GHA workflows on 
    Travis, Jenkins, Gitlab or Circle. [See here for more][ci].
  * **Other Runtimes**. In addition to Docker, Popper can execute 
    workflows in other container runtimes. We currently support 
    [Singularity](https://sylabs.io/) and are working on adding 
    [Podman](https://podman.io) and [Vagrant](https://vagrantup.com/) 
    to the list (see [here for more][runtimedocs]).
  * **Action search**. Provide with a [searchable 
    catalog][search] of publicly available actions so that users can 
    easily find which actions already exist (do not re-invent the 
    wheel!).
  * **Scaffolding**. Aid in the implementation of [new actions and 
    workflows][scaffold].
  * **Action library**. Provide with a list of reusable actions and 
    example workflows <https://github.com/popperized>.

-----

This repository contains:

  * [`cli/`](cli/). The codebase of the command-line tool.
  * [`docs/`](docs/). General [documentation][docs] containing guides, 
    CLI documentation and pointers to other resources.
  * [`gh-pages`][gh-pages] branch. Contents of our [landing 
    page](http://falsifiable.us).

## Installation

To run workflows, you need to have a container runtime installed 
([Docker][docker] and [Singularity][singularity] are currently 
supported). To install Popper you can use 
[`pip`](https://pypi.python.org/pypi). We recommend to install in a 
virtual environment (see [here][venv] for more on `virtualenv`). To 
install:

```bash
pip install popper
```

Once installed, you can get an overview and list of available 
commands:

```bash
popper --help
```

For a Quickstart guide on how to use Popper, look [here][quickstart].

## Contributing

Anyone is welcome to contribute to Popper! To get started, take a look 
at our [contributing guidelines](CONTRIBUTING.md), then dive in with 
our [list of good first 
issues](https://github.com/systemslab/popper/issues?utf8=%E2%9C%93&q=is%3Aissue+label%3A%22good+first+issue%22+is%3Aopen) 
and [open projects](https://github.com/systemslab/popper/projects).

## Participation Guidelines

Popper adheres to the code of conduct [posted in this 
repository](CODE_OF_CONDUCT.md). By participating or contributing to 
Popper, you're expected to uphold this code. If you encounter 
unacceptable behavior, please immediately [email 
us](mailto:ivo@cs.ucsc.edu).

[singularity]: https://github.com/sylabs/singularity
[docker]: https://get.docker.com
[quickstart]: https://popper.readthedocs.io/en/latest/sections/getting_started.html
[venv]: https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/#installing-virtualenv
[ci]: https://medium.com/getpopper/waiting-for-your-github-actions-invite-wait-no-longer-cf310b8c630c
[popper2]: https://github.com/systemslab/popper/projects/12
[search]: https://medium.com/getpopper/searching-for-existing-github-actions-has-never-been-easier-268c463f0257
[docs]: https://popper.readthedocs.io/en/latest/
[gh-pages]: https://github.com/systemslab/popper/tree/gh-pages
[scaffold]: https://popper.readthedocs.io/en/latest/sections/getting_started.html#create-a-workflow
[runtimedocs]: https://popper.readthedocs.io/en/latest/sections/extensions.html#other-runtimes
[hcl-to-yml]: 
