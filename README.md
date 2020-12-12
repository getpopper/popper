# <img src="https://raw.githubusercontent.com/getpopper/website/bcba4c8/assets/images/popper_logo_just_jug.png" width="64" valign="middle" alt="Popper"/> Popper

[![Downloads](https://pepy.tech/badge/popper)](https://pepy.tech/project/popper)
[![Build Status](https://travis-ci.org/getpopper/popper.svg?branch=master)](https://travis-ci.org/getpopper/popper)
[![codecov](https://codecov.io/gh/getpopper/popper/branch/master/graph/badge.svg)](https://codecov.io/gh/getpopper/popper)
[![Join the chat at https://gitter.im/systemslab/popper](https://badges.gitter.im/systemslab/popper.svg)](https://gitter.im/falsifiable-us/popper?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)
[![slack](https://img.shields.io/badge/chat-on_slack-C03C20.svg?logo=slack)](https://join.slack.com/t/getpopper/shared_invite/zt-dtn0se2s-c50myMHNpeoikQXDeNbPew)
[![CROSS](https://img.shields.io/badge/supported%20by-CROSS-green)](https://cross.ucsc.edu)

Popper is a tool for defining and executing container-native testing workflows in Docker. 
With Popper, you define a workflow in a YAML file, and then execute it with a single command. 
A workflow file looks like this:

```yaml
steps:
- id: dev-init
  uses: docker://rikorose/gcc-cmake:gcc-9
  runs: [sh, -uexc]
  args:
  - |
    rm -rf build/
    cmake -DCMAKE_BUILD_TYPE=Release -S . -B build

- id: build
  uses: docker://rikorose/gcc-cmake:gcc-9
  runs: [cmake, --build, build/, --parallel, '4']

- id: test
  uses: docker://rikorose/gcc-cmake:gcc-9
  dir: /workspace/build/
  runs: [ctest]
```

Assuming the above is stored in a `ci.yml` file in the root of the (C++) project, this entire workflow gets executed by running:

```bash
popper run -f ci.yml
```

Running a single step:

```bash
popper run -f ci.yml build
```

Starting a shell inside the `build` step container:

```bash
popper run -f ci.yml build
```

Running on another engine (Podman):

```bash
popper run -f ci.yml -e podman build
```

The [`examples/`](./examples) folder contains workflow starters for other languages, as well as other types of tests (integration, regression, enduring, etc.).

## Installation

To install or upgrade Popper, run the following in your terminal:

```bash
curl -sSfL https://raw.githubusercontent.com/getpopper/popper/master/install.sh | sh
```

[Docker][docker] is required to run Popper and the installer will 
abort if the `docker` command cannot be invoked from your shell. For 
other installation options, including installing for use with the 
other supported engines (Singularity and Podman), or for setting up a 
developing environment for Popper, [read the complete installation 
instructions][installation].

Once installed, you can get an overview and list of available 
commands:

```bash
popper help
```

Read the [Quickstart Guide][getting_started] to learn the basics of 
how to use Popper. Or browse the [Official documentation][docs].

## Features

  * **Lightweight workflow and task automation syntax.** Defining a list of 
    steps is as simple as writing file in a [lightweight YAML syntax][cnwf] and 
    invoking `popper run` (see demo above). If you're familiar with 
    [Docker Compose][compose], you can think of Popper as Compose but 
    for end-to-end tasks instead of services.

  * **An abstraction over container runtimes**. In addition to Docker, 
    Popper can seamlessly execute workflows in other runtimes by 
    interacting with distinct container engines. Popper currently 
    supports [Docker][docker], [Singularity][sylabs] and 
    [Podman][podman].

  * **An abstraction over CI services**. Define a pipeline once and 
    then instruct Popper to generate configuration files for distinct 
    CI services, allowing users to run the exact same workflows they 
    run locally on Travis, Jenkins, Gitlab, Circle and others. See the 
    [`examples/`](./examples/) folder for examples on how to automate 
    CI tasks for multiple projects (Go, C++, Node, etc.).

  * **An abstraction over resource managers**. Popper can also execute 
    workflows on a variety of resource managers and schedulers such as 
    Kubernetes and SLURM, without requiring any modifications to a 
    workflow YAML file. We currently support SLURM and are working on 
    adding support for Kubernetes.

  * **Aid in workflow development**. Aid in the implementation and 
    [debugging][pp-sh] of workflows, and provide with an extensive 
    list of [example 
    workflows](https://github.com/getpopper/popper-examples) that can 
    serve as a starting point.

## What Problem Does Popper Solve?

Popper is a container-native workflow execution and task automation 
engine. In practice, when we work following the 
[container-native](docs/sections/concepts.md) paradigm, we end up 
interactively executing multiple Docker commands (`docker pull`, 
`docker build`, `docker run`, etc.) so that we can build containers, 
compile code, test applications, deploy software, among others. 
Keeping track of which `docker` commands we have executed, in which 
order, and which flags were passed to each, can quickly become 
unmanageable, difficult to document (think of outdated README 
instructions) and error prone.

On top of this, having the same workflow work in other environments 
(CI, K8S, etc.) is time-consuming and defeats the purpose of using 
containers (portability). The goal of Popper is to bring order to this 
chaotic scenario by providing a framework for clearly and explicitly 
defining container-native tasks. You can think of Popper as tool for 
wrapping all these manual tasks in a lightweight, machine-readable, 
self-documented format (YAML).

While this sounds simple at first, it has significant implications: 
results in time-savings, improves communication and in general unifies 
development, testing and deployment workflows. As a developer or user 
of "Popperized" container-native projects, you only need to learn one 
tool, and leave the execution details to Popper, whether is to build 
and tests applications locally, on a remote CI server or a Kubernetes 
cluster.

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

> Ivo Jimenez, Michael Sevilla, Noah Watkins, Carlos Maltzahn, Jay 
> Lofstead, Kathryn Mohror, Andrea Arpaci-Dusseau and Remzi 
> Arpaci-Dusseau. _The Popper Convention: Making Reproducible Systems 
> Evaluation Practical_. In 2017 IEEE International Parallel and 
> Distributed Processing Symposium Workshops (IPDPSW), 1561–70, 2017. 
> (https://doi.org/10.1109/IPDPSW.2017.157)

PDF for a pre-print version [available here](https://raw.githubusercontent.com/systemslab/popper-paper/master/paper/paper.pdf). 
For BibTeX, [click here](https://raw.githubusercontent.com/systemslab/popper-paper/master/popper.bib).

[gfi]: https://github.com/getpopper/popper/issues?utf8=%E2%9C%93&q=is%3Aissue+label%3A%22good+first+issue%22+is%3Aopen
[docker]: https://docs.docker.com/get-docker/
[getting_started]: https://popper.readthedocs.io/en/latest/sections/getting_started.html
[docs]: https://popper.readthedocs.io/en/latest/
[sylabs]: https://sylabs.io/
[compose]: https://docs.docker.com/compose/
[podman]: https://podman.io
[pp-sh]: docs/sections/cli_features.md#executing-a-step-interactively
[installation]: docs/installation.md
[cnwf]: ./docs/sections/cn_workflows.md#syntax
