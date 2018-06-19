# Concepts

## Scientific exploration pipelines

Over the last decade software engineering and systems administration 
communities (also referred to as 
[DevOps](https://en.wikipedia.org/wiki/DevOps)) have developed 
sophisticated techniques and strategies to ensure “software 
reproducibility”, i.e. the reproducibility of software artifacts and 
their behavior using versioning, dependency management, 
containerization, orchestration, monitoring, testing and 
documentation. The key idea behind the Popper protocol is to manage 
every experiment in computation and data exploration as a software 
project, using tools and services that are readily available now and 
enjoy wide popularity. By doing so, scientific explorations become 
reproducible with the same convenience, efficiency, and scalability as 
software repeatable while fully leveraging continuing improvements to 
these tools and services. Rather than mandating a particular set of 
tools, the convention only expects components of an experiment to be 
scripted. There are two main goals for Popper:

 1. It should be usable in as many research projects as possible, 
    regardless of their domain.
 2. It should abstract underlying technologies without requiring a 
    strict set of tools, making it possible to apply it on multiple 
    toolchains.

### Popper Pipelines

A common generic analysis/experimentation workflow involving a 
computational component is the one shown below. We refer to this as a 
pipeline in order to abstract from experiments, simulations, analysis 
and other types of scientific explorations. Although there are some 
projects that don't fit this description, we focus on this model since 
it covers a large portion of pipelines out there. Typically, the 
implementation and documentation of a scientific exploration is 
commonly done in an ad-hoc way (custom bash scripts, storing in local 
archives, etc.).

![Experimentation Workflow. The analogy of a lab notebook in 
experimental sciences is to document an experiment's evolution. This 
is rarely done and, if done, usually in an ad-hoc way (an actual 
notebook or a text file).](/figures/workflow.png)

The idea behind Popper is simple: make an article self-contained by 
including in a code repository the manuscript along with every 
experiment's scripts, inputs, parametrization, results and validation. 
To this end we propose leveraging state-of-the-art technologies and 
applying a DevOps approach to the implementation of scientific 
pipelines (also referred to 
[SciOps](https://en.wikipedia.org/wiki/DevOps#Scientific_DevOps_(SciOps))).

![DevOps approach to Implementing Scientific Explorations, also 
referred to as SciOps.](/figures/workflow_devops.png)

Popper is a convention (or protocol) that maps the implementation of a 
pipeline to software engineering (and DevOps/SciOps) best-practices 
followed in open-source software projects. If a pipeline is 
implemented by following the Popper convention, we call it a 
popper-compliant pipeline or popper pipeline for short. A popper 
pipeline is implemented using DevOps tools (e.g., version-control 
systems, lightweight OS-level virtualization, automated multi-node 
orchestration, continuous integration and web-based data 
visualization), which makes it easier to re-execute and validate.

We say that an article (or a repository) is Popper-compliant if its 
scripts, dependencies, parameterization, results and validations are 
all in the same respository (i.e., the pipeline is self-contained). If 
resources are available, one should be able to easily re-execute a 
popper pipeline in its entirety. Additionally, the commit log becomes 
the lab notebook, which makes the history of changes made to it 
available to readers, an invaluable tool to learn from others and 
"stand on the shoulder of giants". A "popperized" pipeline also makes 
it easier to advance the state-of-the-art, since it becomes easier to 
extend existing work by applying the same model of development in OSS 
(fork, make changes, publish new findings).

### Repository Structure

The general repository structure is simple: a `paper` and `pipelines` 
folders on the root of the project with one subfolder per pipeline

```bash
$> tree mypaper/
├── pipelines
│   ├── exp1
│   │   ├── README.md
│   │   ├── output
│   │   │   ├── exp1.csv
│   │   │   ├── post.sh
│   │   │   └── view.ipynb
│   │   ├── run.sh
│   │   ├── setup.sh
│   │   ├── teardown.sh
│   │   └── validate.sh
│   ├── analysis1
│   │   ├── README.md
│   │   └── ...
│   └── analysis2
│       ├── README.md
│       └── ...
└── paper
    ├── build.sh
    ├── figures/
    ├── paper.tex
    └── refs.bib
```

### Pipeline Folder Structure

A minimal pipeline folder structure for an experiment or analysis is 
shown below:

```{#lst:repo .bash caption="Basic structure of a Popper repository."}
$> tree -a paper-repo/pipelines/myexp
paper-repo/pipelines/myexp/
├── README.md
├── post-run.sh
├── run.sh
├── setup.sh
├── teardown.sh
└── validate.sh
```

Every pipeline has `setup.sh`, `run.sh`, `post-run.sh`, `validate.sh` 
and `teardown.sh` scripts that serve as the entrypoints to each of the 
stages of a pipeline. All these return non-zero exit codes if there's 
a failure. In the case of `validate.sh`, this script should print to 
standard output one line per validation, denoting whether a validation 
passed or not. In general, the form for validation results is 
`[true|false] <statement>` (see examples below).

```{#lst:validations .bash caption="Example output of validations."}
[true]  algorithm A outperforms B
[false] network throughput is 2x the IO bandwidth
```

The [CLI](https://github.com/systemslab/popper/popper) tool includes a 
`pipeline init` subcommand that can be executed to scaffold a pipeline 
with the above structure. The syntax of this command is:

```bash
popper pipeline init <name>
```

Where `<name>` is the name of the pipeline to initialize. More details 
on how pipelines are executed is presented in the next section.

## Pipeline portability

**TODO**

## Continuous Validation of Pipelines

**TODO**

## Popper vs. Other Software

With the goal of putting Popper in context, the following is a list of 
comparisons with other existing tools.

### Scientific Workflow Engines

[Scientific workflow 
engines](https://en.wikipedia.org/wiki/Scientific_workflow_system) are 
"a specialized form of a workflow management system designed 
specifically to compose and execute a series of computational or data 
manipulation steps, or workflow, in a scientific application." 
[Taverna](https://taverna.incubator.apache.org/) and
[Pegasus](https://pegasus.isi.edu/) are examples of widely used 
scientific workflow engines. For a comprehensive list, see 
[here](https://github.com/pditommaso/awesome-pipeline).

A Popper pipeline can be seen as the highest-level workflow of a 
scientific exploration, the one which users or automation services 
interact with (which can be visualized by doing `popper workflow`). A 
stage in a popper pipeline can itself trigger the execution of a 
workflow on one of the aforementioned workflow engines. A way to 
visualize this is shown in the following image:

![](/figures/popper_pipeline_vs_workflow_engine.png)

The above corresponds to a pipeline whose `run.sh` stage triggers the 
execution of a workflow for a numeric weather prediction setup (the 
code is available [here](https://github.com/popperized/nwp-popper)). 
Ideally, the workflow specification files (e.g. in 
[CWP](http://www.commonwl.org/) format) would be stored in the 
repository and be passed as parameter in a bash script that is part of 
a popper pipeline. For an example of a popper pipeline using the 
[Toil](https://github.com/BD2KGenomics/toil) genomics workflow engine, 
see [here](https://github.com/popperized/PopperCI_Toil).

### Virtualenv, Conda, Packrat, etc.

Language runtime-specific tools for Python, R, and others, provide the 
ability of recreating and isolating environments with all the 
dependencies that are needed by an application that is written in one 
of these languages. For example 
[`virtualenv`](https://virtualenv.pypa.io/) can be used to create an 
isolated environment with all the dependencies of a python 
application, including the version of the python runtime itself. This 
is a lightweight way of creating portable pipelines.

Popper pipelines automate and create an explicit record of the steps 
that need to be followed in order to create these isolated 
environments. For an example of a pipeline of this kind, see [here]().

For pipelines that execute programs written in statically typed 
languages (e.g. C++), these types of tools are not a good fit and 
other "full system" virtualization solutions such as Docker or Vagrant 
might be a better alternative. For an example of such a pipeline, see 
[here](https://github.com/popperized/nwp-popper).

### CI systems

Continuous Integration (CI) is a development practice that requires 
developers to integrate code into a shared repository frequently with 
the purpose of catching errors as early as possible. The pipelines 
associated with an article can also benefit from CI. If the output of 
a pipeline can be verified and validated by codifying any expectation, 
in the form of a unit test (a command returning a boolean value), this 
can be verified on every change to a pipeline repository.

[Travis CI](https://travis-ci.org/) is an open-source, hosted, 
distributed continuous integration service used to build and test 
software projects hosted at GitHub. Alternatives to Travis CI are 
[CircleCI](https://circleci.com) and [CodeShip](https://codeship.com). 
Other self-hosted solutions exist such as 
[Jenkins](http://jenkins-ci.org). Each of these services require users 
to specify and automate tests using their own configuration files (or 
domain specific languages).

Popper can be seen as a service-agnostic way of automating tests that 
can run on multiple CI services with minimal effort. The `popper ci` 
command [generates configuration 
files](http://popper.readthedocs.io/en/latest/ci/popperci.html#ci-system-configuration) 
that existing CI systems read in order to execute a popper pipeline. 
Additionally, with most of existing tools and services, users don't 
have a way of easily checking the integrity of a pipeline locally, 
whereas Popper can be used easily to [test a pipeline 
locally](http://popper.readthedocs.io/en/latest/ci/popperci.html#testing-locally). 
Lastly, since the concept of a pipeline and validations associated to 
them is a first-class citizen in Popper, we can not only check that a 
pipeline can execute correctly (SUCCESS or FAILURE) but we can also 
[verify that the output is the one 
expected](http://popper.readthedocs.io/en/latest/ci/popperci.html#ci-functionality) 
by the original implementers.

### Reprozip / Sciunit

[Reprozip](https://www.reprozip.org/) "allows you to pack your 
research along with all necessary data files, libraries, environment 
variables and options", while [Sciunit](sciunit.run) "are efficient, 
lightweight, self-contained packages of computational experiments that 
can be guaranteed to repeat or reproduce regardless of deployment 
issues". They accomplish this by making use of 
[`ptrace`](https://en.wikipedia.org/wiki/Ptrace) to track all 
dependencies of an application.

Popper can help in automating the tasks required to install 
Reprozip/Sciunit, as well as to create and execute Reprozip packages 
and Sciunits. However, a Popper pipeline is already self-contained and 
can be made portable by explicitly using language (e.g. virtualenv), 
OS-level (e.g. Singularity) or hardware (e.g. Virtualbox) 
virtualization tools. In these cases, using Reprozip or Sciunit would 
be redundant, since they make use of Docker or Vagrant "underneath the 
covers" in order to provide portable experiment packages/units.
