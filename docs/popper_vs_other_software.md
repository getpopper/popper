# Popper vs. Other Software

With the goal of putting Popper in context, the following is a list of 
comparisons with other existing tools.

## Scientific Workflow Engines

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

## Virtualenv, Conda, Packrat, etc.

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

## CI systems

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

## Reprozip / Sciunit

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
