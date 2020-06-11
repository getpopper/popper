# <img src="https://raw.githubusercontent.com/getpopper/website/bcba4c8/assets/images/popper_logo_just_jug.png" width="64" valign="middle" alt="Popper"/> Popper

[![Downloads](https://pepy.tech/badge/popper)](https://pepy.tech/project/popper)
[![Build Status](https://travis-ci.org/getpopper/popper.svg?branch=master)](https://travis-ci.org/getpopper/popper)
[![codecov](https://codecov.io/gh/systemslab/popper/branch/master/graph/badge.svg)](https://codecov.io/gh/systemslab/popper)
[![black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)
[![PyPI version](https://badge.fury.io/py/popper.svg)](https://badge.fury.io/py/popper)
[![Join the chat at https://gitter.im/systemslab/popper](https://badges.gitter.im/systemslab/popper.svg)](https://gitter.im/falsifiable-us/popper?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)
[![slack](https://img.shields.io/badge/chat-on_slack-C03C20.svg?logo=slack)](https://join.slack.com/t/getpopper/shared_invite/zt-dtn0se2s-c50myMHNpeoikQXDeNbPew)

Popper is a tool for defining and executing container-native workflows in 
Docker, as well as other container engines. With Popper, you define a workflow 
in a YAML file, and then execute it with a single command. A workflow file looks 
like this:

```yaml
steps:
# download CSV file with data on global CO2 emissions
- id: download
  uses: docker://byrnedo/alpine-curl:0.1.8
  args: [-LO, https://github.com/datasets/co2-fossil-global/raw/master/global.csv]

# obtain the transpose of the global CO2 emissions table
- id: get-transpose
  uses: docker://getpopper/csvtool:2.4
  args: [transpose, global.csv, -o, global_transposed.csv]
```

Assuming the above is stored in a `wf.yml` file, the workflow gets executed by 
running:

```bash
popper run -f wf.yml
```

Or run a single single step by doing:

```bash
popper run -f wf.yml get-transpose
```

Keep reading down to find [installation instructions](#installation). For more 
information on the YAML syntax, [see here][cnwf].

The high-level goals of this project are:

  * **Lightweight workflow and task automation syntax.** Defining a list of 
    steps is as simple as writing file in a [lightweight YAML syntax][cnwf] and 
    invoking `popper run` (see demo above). If you're familiar with [Docker 
    Compose][compose], you can think of Popper as Compose but for workflows 
    instead of services.
  * **An abstraction over container runtimes**. In addition to Docker, 
    Popper can seamlessly execute workflows in other runtimes by 
    interacting with distinct container engines. Popper currently 
    supports [Singularity][sylabs] and we are working on adding 
    [Podman][podman].
  * **Run on distinct resource managers**. Popper can also execute workflows on 
    a variety of resource managers and schedulers such as Kubernetes and SLURM, 
    without requiring any modifications to a workflow YAML file. We currently 
    support SLURM and are working on adding support for Kubernetes.
  * **Continuous integration**. Generate configuration files for 
    distinct CI services, allowing users to run the exact same workflows they 
    run locally on Travis, Jenkins, Gitlab, Circle and others. See the 
    [`examples/`](./examples/ci/) folder for examples on how to automate CI 
    tasks for multiple projects (Go, C++, Node, etc.).
  * **Workflow development**. Aid in the implementation and [debugging][pp-sh] 
    of workflows, and provide with an extensive list of [example 
    workflows](https://github.com/popperized) that can serve as a starting 
    point.

-----

This repository contains:

  * [`docs/`](docs/). General [documentation][docs] containing guides, 
    CLI documentation and pointers to other resources.
  * [`examples/`](examples/). Workflow examples that can be used as 
    starting points. More complex examples are available on [this 
    repository](https://github.com/getpopper/popper-examples).
  * [`src/`](src/). The codebase of the command-line tool.
  * [`install.sh`](./install.sh). The Popper installer.

## What Problem Does Popper Solve?

Popper is a [container-native][cn] workflow execution and task automation 
[engine][wfeng]. In practice, when we work following the container-native 
paradigm, we end up executing a bunch of `docker pull|build|run` commands in 
order to get stuff done. Keeping track of which `docker` commands we have 
executed, in which order, and which flags were passed to each, can quickly 
become unmanageable, difficult to document (think of outdated README 
instructions) and error prone.

The goal of Popper is to streamline this process by providing a framework for 
clearly and explicitly defining container-native tasks, including the order in 
which these tasks are supposed to be executed. You can think of this as a 
lightweight, machine-readable wrapper (YAML) around what would otherwise be 
manually executed docker commands.

While this seems simple at first, it has great implications: Popper allows to 
unify development, testing, and deployment workflows, resulting in:

  * Communication improvements.
  * Time savings. Reduced amount of time it takes for contributors to get 
  onboard.
  * Reduced tooling, one single automation tool for development and CI.

## Installation

To install or upgrade Popper, run the following in your terminal:

```bash
curl -sSfL https://raw.githubusercontent.com/getpopper/popper/master/install.sh | sh
```

[Docker][docker] is required to run Popper and the installer will abort if the 
`docker` command cannot be invoked from your shell. The installer script informs 
of what is about to do and asks for permission before proceeding. Once 
installed, you can get an overview and list of available commands:

```bash
popper --help
```

Read the [Quickstart Guide][getting_started] to learn the basics of how to use 
Popper. For other installation options, including installing for use with 
Singularity or for setting up a developing environment for Popper, [see 
here][installation].

## Contributing

Anyone is welcome to contribute to Popper! To get started, take a look 
at our [contributing guidelines](CONTRIBUTING.md), then dive in with 
our [list of good first issues][gfi].

## Participation Guidelines

Popper adheres to the code of conduct [posted in this 
repository](CODE_OF_CONDUCT.md). By participating or contributing to 
Popper, you're expected to uphold this code. If you encounter unacceptable 
behavior, please immediately [email us](mailto:ivotron@ucsc.edu).

## How to Cite Popper

Ivo Jimenez, Michael Sevilla, Noah Watkins, Carlos Maltzahn, Jay 
Lofstead, Kathryn Mohror, Andrea Arpaci-Dusseau and Remzi 
Arpaci-Dusseau. _The Popper Convention: Making Reproducible Systems 
Evaluation Practical_. In 2017 IEEE International Parallel and 
Distributed Processing Symposium Workshops (IPDPSW), 1561–70, 2017. 
https://doi.org/10.1109/IPDPSW.2017.157.

For BibTeX, click [here](https://falsifiable.us/pubs/bibtex/popper.bib).

[minimalpy]: https://github.com/popperized/popper-examples/tree/master/workflows/minimal-python
[gfi]: https://github.com/systemslab/popper/issues?utf8=%E2%9C%93&q=is%3Aissue+label%3A%22good+first+issue%22+is%3Aopen
[singularity]: https://github.com/sylabs/singularity
[docker]: https://get.docker.com
[getting_started]: https://popper.readthedocs.io/en/latest/sections/getting_started.html
[venv]: https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/#installing-virtualenv
[popper2]: https://github.com/systemslab/popper/projects/12
[docs]: https://popper.readthedocs.io/en/latest/
[gh-pages]: https://github.com/systemslab/popper/tree/gh-pages
[cnwf]: docs/sections/cn_workflows.md
[engines]: docs/sections/cn_workflows.md#container-engines
[sylabs]: https://sylabs.io/
[cn]: https://cloudblogs.microsoft.com/opensource/2018/04/23/5-reasons-you-should-be-doing-container-native-development/
[compose]: https://docs.docker.com/compose/
[podman]: https://podman.io
[minimalpython]: https://github.com/popperized/popper-examples/tree/master/workflows/minimal-python
[pp-sh]: docs/sections/cli_features.md#executing-a-step-interactively
[installation]: docs/installation.md
