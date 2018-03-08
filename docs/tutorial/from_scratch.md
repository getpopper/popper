## Implementing an Experiment

This guide shows how to follow Popper when carrying out a scientific 
exploration. We will use the experimentation workflow shown below to 
guide our discussion. We assume that the only artifact available at 
the beginning of the exploration is the piece of code (leftmost 
component in the diagram) that is used as the basis of our study (e.g. 
a system, a simulation, analysis code, etc.).

Before we implement the code related to our exploration, we need to 
decide which tools we will use for each of the components of the 
workflow. A concrete list of steps that we follow:

 1. Decide how to package the code.
 2. Write the experiment steps in a script.
 3. For big input/output datasets, codify their management.
 4. Script the analysis and visualization of results.
 5. Specify the validation criteria and codify it if possible.
 6. Automate the generation of a manuscript (if any).

In the following we explore each steps in more detail. For examples of 
already "Popperized" explorations, take a look at 
[here](../protocols/getting_started.html#guides-and-examples).

![DevOps approach to Experiments.](/figures/workflow_devops.png)

### The Popper Repository

The first thing is to create the repository that will hold all the 
experiment assets. Any version-control tool can serve this purpose. We 
recommend using Git or Mercurial, mainly because these have web 
interfaces that are popular and easy to use (e.g. 
[Github](https://github.com), [GitLab](https://gitlab.com/explore) or 
[Bitbucket](https://bitbucket.org)). To create a repository using Git:

```bash
mkdir mypaper
cd mypaper
git init
echo "# My Paper Repo" > README.md
git commit -m "First commit of my paper repo."
```

See 
[here](https://help.github.com/articles/good-resources-for-learning-git-and-github/) 
for a list of resources for learning git. Once a git repo exists, we 
proceed to add the assets associated with an experiment.

It's important to keep in mind that the commit log (messages 
associated to every change) of the Git repository serves the purpose 
of a [labnotebook](https://en.wikipedia.org/wiki/Lab_notebook). It's 
useful to follow [general commit 
guidelines](http://gitforteams.com/resources/commit-granularity.html) 
that that apply for any kind of project, with the exception of trying 
to be as verbose and explicit as possible to make it easier for others 
to understand what are the changes in a commit, from the point of view 
of the experimentation process.

### Packaging

Usually the piece of code that is used as the basis of study resides 
in its own repository. Instead of bringing that entire codebase to the 
Popper repository, it's better to reference a 
package<sup>[1](#myfootnote1)</sup> in the experiment scripts. In this 
way, the maintenance of the code and experiment logic can be kept 
separate.

<a name="myfootnote1">1</a>: By package, we mean any medium through 
which a piece of software is delivered to its end users. This 
definition is generic enough that covers traditional OS package 
managers, but also other types of packaging, such as dynamic language 
packages (e.g. `pip`), Virtual Machines and Linux containers.

If a package for the codebase in question is not available, there are 
quick ways to generate a packaged version of the code. One such way is 
to use 
[Docker](https://docs.docker.com/engine/tutorials/dockerimages/) to 
package it. For example, in [this](math-science.html) experiment we 
make use of [a library](https://github.com/flame/blis) by creating a 
[Docker image](https://github.com/ivotron/docker-blis) that we 
reference in the [experiment 
script](https://github.com/systemslab/popper/blob/master/templates/experiments/blis/run.sh).

The main goal of the packaging step is to end up with a "black box" 
that we use as part of our experiment. We pass it experiment 
parameters (variable values and input datasets) and we obtain results:

```
 params     ------   output
---------> | code | -------->
            ------
```

### Scripting The Experiment

Our goal is to codify the series of steps that are taken as part of 
the experiment. For obtaining the structure of an experiment 
folder:

```bash
popper init myexperiment
```

For experiments that run in a local machine, 
[`bash`](https://www.gnu.org/software/bash/) is sufficient (see 
example 
[here](https://github.com/systemslab/popper/blob/master/templates/experiments/mpip/run.sh)). 
For multi-node experiments, a tool like 
[Ansible](https://github.com/ansible/ansible) can be used to 
orchestrate the experiment (see example 
[here](https://github.com/ivotron/torpor-popper/tree/master/experiments/base-vs-limited-targets)). 
In any case, these scripts should be added to the Popper (Git) 
repository.

### Dataset Management

For small input (or output) datasets consumed (or generated) by the 
experiment, they can be added to the repository along with the 
experiment scripts. It's important to make these available so that 
other people can compare when repeating an experiment. Typical file 
formats used in practice while obtaining experiment results are CSV or 
JSON files. When datasets are [too 
big](https://help.github.com/articles/working-with-large-files/) to be 
efficiently managed by Git, other tools can be used. Examples are 
[GitLFS](https://git-lfs.github.com/) or 
[Datapackages](http://frictionlessdata.io/data-packages/). For an 
example of an experiment using Datapackages, take a look 
[here](data-science.html#adding-more-datasets).

As mentioned before, when committing changes to the Popper (Git) 
repository, it is a good practice to separate commits that affect the 
logic of the experiment from those that add new results.

### Analysis and Visualization

Visualizing and analyzing output data should be done with tools that 
allow to be scripted. Examples are the wide category of "notebooks" 
such as [Jupyter](http://jupter.org), 
[Zeppelin](http://zeppelin.apache.org/), 
[Beaker](http://beakernotebook.com/), among others. For an example of 
an experiment using a notebook, see 
[here](https://github.com/systemslab/popper/blob/master/templates/experiments/blis/results/visualize.ipynb).

An alternative to notebooks is to use sites such as 
[Plot.ly](https://plot.ly/) or 
[Tableau](http://www.tableau.com/products/cloud-bi) that provide 
analysis and visualization "as a service". The main features that 
tools in this category have to support is to allow for scripts to be 
provided and results to be obtained and retrieved so that they can be 
stored in the Popper (Git) repository. It is good practice to have a 
single commit to represent both the change to raw results (output 
datasets) and the visualization of such results (image files).

### Adding Validation Criteria

Integrity of the experimental results. These domain-specific tests 
ensure that the claims made in the paper are valid for every 
re-execution of the experiment, analogous to performance regression 
tests done in software projects. Alternatively, claims can also be 
corroborated as part of the analysis code. When experiments are not 
sensitive to the effects of virtualized platforms, these assertions 
can be executed on public/free [continuous 
integration](https://en.wikipedia.org/wiki/Continuous_integration) 
platforms (e.g. [TravisCI](https://travis-ci.org) runs tests in VMs). 

However, when results are sensitive to the underlying hardware, it is 
preferable to leave this out of the CI pipeline and make them part of 
the post-processing routines of the experiment. High-level languages 
can be used to corroborate claims made against output results. 
[Aver](https://github.com/ivotron/aver) is an example of such a 
language that can express these type of assertions and also can be use 
to check their validity. Examples of these type of statements are: 
"the runtime of our algorithm is 10x better than the baseline when the 
level of parallelism exceeds 4 concurrent threads"; or "for dataset A, 
our model predicts the outcome with an error of 95%". For an example, 
check [here](https://github.com/ivotron/aver#overview).

### Reporting Results

Any markup language can be used for reporting results. Markdown or 
LATeX are examples. For LATeX, ideally one would like to include all 
the dependencies that are needed to generate the publishable format of 
the manuscript (e.g. PDF). An alternative is to provide a VM or Docker 
image with all the dependencies in such a way that readers don't need 
to manage the installation and configuration of the markup language 
processor. For examples, see
[here](https://github.com/popperized/popper-readthedocs-examples/).
