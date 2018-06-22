# Examples

In this section we present a examples of Popper pipelines. All these 
are available on github and can be added to a local repo by doing:

```bash
popper add popperized/<repo>/<pipeline>
```

Where `<repo>` is the name of the repository where a pipeline is 
contained, and `<pipeline>` is the name of the pipeline.

## Pipeline portability

**TODO**

### Using Virtualenv (Python)

**TODO**

### Using Packrat (R)

**TODO**

### Using Spack

**TODO**

### Using Docker

In recent years, [Docker](https://www.docker.com/) has emerged in the devops
world as a powerful tool for for builiding and using versatile reusable
environments for development and deployment. We can leverage Docker to run our
experiments in isolated and easily recreatable environments. In this example
we'll build a pipeline for a simple data science experiment using whose only
requirement on the host machine is having `docker` installed. You can find
instructions on installing Docker at the [official
website](https://docs.docker.com/install/).


The directory structure for this pipeline is as follows:

```
docker-data-science
├── setup.sh
├── analyze.sh
├── analyze.sh
├── generate-figures.sh
└── docker
    ├── Dockerfile
    ├── requirements.txt
    ├── app.py
    └── generate-figures.py
```

We have three stages as well as a directory for our docker image, including the
two python scripts we want to run: `app.py`, and `generate_figures.py`. The
setup stage builds the docker image, installing and setting up the dependencies
specified in our `requirements.txt` file, while each of the other two stages
will run one of the two scripts inside the container, ouputting results inside
a `results` directory. This example can be found in full
[here](https://github.com/popperized/popper-readthedocs-examples/tree/master/pipelines/docker-data-science),
and is also explored in greater depth in this [Software Carpentry
lesson](https://popperized.github.io/swc-lesson/05-pipeline-portability-with-docker/index.html).

Using this comparmentalized splitting of stages and keeping our dependencies
inside docker, we become capable of sharing our experiments with whomever we
want. In addition to this, we can also do other things, such as validating your
experiments on every commit, as seen in the continous validation section of this
documentation.

### Using Vagrant

**TODO**

## Dataset Management

### Using Datapackages

**TODO**

### Using data.world

**TODO**

## Infrastructure automation


### On CloudLab using geni-lib

**TODO**

### On Chameleon using enos

**TODO**

### On EC2/GCE using terraform

**TODO**

## Domain-specific pipelines

### Atmospheric science

**TODO**

### Machine learning

**TODO**

### Linux kernel development

**TODO**

### Relational databases

**TODO**

### Distributed file systems

**TODO**

### Genomics

**TODO**

### High energy physics

**TODO**

### Applied Mathematical Science

[BLIS](https://github.com/flame/blis) is a portable software framework
for instantiating high-performance BLAS-like dense linear algebra
libraries. This experiment corresponds to the one presented in the
[first BLIS paper](http://doi.acm.org/10.1145/2764454). A [subsequent
report](http://dl.acm.org/citation.cfm?id=2738033) documents how to
repeat this experiment. This pipeline corresponds to sections
2.1-2.3 of the replicability report and consists of three stages:

  * `build-docker-image`. [A Docker
    image](https://github.com/ivotron/docker-blis/tree/master/Dockerfile)
    prepares all the binaries for BLIS, OpenBLAS and Atlas
    precompiled.
  * `run`. Executes the experiment that compares BLIS against other
    BLAS implementations, generating output to the `results/` folder.
  * `analyze`. Runs the analysis on the output of the experiment,
    corresponding to figures 13-15 from the original paper. To
    visualize results locally, one can execute the following:

    ```bash
    docker run -d \
      -v `pwd`:/code/experiment -p 8888:8888  jupter notebook
      --NotebookApp.token=""
    ```

    After the above executes, open Browser and point it to
    <http://localhost:8888>. To see an example of how the notebook looks
    click
    [here](https://github.com/popperized/popper-readthedocs-examples/blob/master/pipelines/blis/results/visualize.ipynb).

The pipeline is available on github at [this
repository](https://github.com/popperized/popper-readthedocs-examples/master/pipelines/blis).

### High Performance Computing

A typical experiment in HPC assumes many things from the 
environment: an NFS mount point available in compute nodes, a batch 
scheduler, applications installed/compiled directly on the host (i.e. 
without any type of virtualization), among others. In this case, 
Popper is followed to record the scripts used to compile, install and 
run the experiment, as well as analyze its results. We assume SLURM as 
the batch scheduler and use spack to install the software stack.

We assume that the `$HOME/mypaper` folder is available in the users' 
laptop as well as on the nodes of the machine where the experiment 
runs.

The experiment corresponds to an execution of the 
[LULESH](https://codesign.llnl.gov/lulesh.php) MPI [proxy 
application](http://www.lanl.gov/projects/codesign/proxy-apps/assets/docs/proxyapps_strategy.pdf)
compiled against [mpiP](http://mpip.sourceforge.net/). The experiment 
consists of three stages:

  * `install` installs the dependencies via [`spack`](https://github.com/llnl/spack). 
    Since `spack` installs 
    dependencies from source, the `install` stage should be executed 
    in a node with the same architecture as the one of the compute 
    nodes where LULESH will run (e.g. in a "head" node of the 
    machine).

  * `run`. Executes LULESH by sending the job to the SLURM batch 
    scheduler.

  * `analyze`. Post-process the results that are gathered by `mpiP`. 
    Once the experiment finishes, `mpiP` places a text file in the 
    `results/` folder (a text file file ending in `.mpiP`) that 
    contains MPI runtime metrics. The `analyze.sh` script launches a 
    [Jupyter](http://jupyter.org/) notebook server (using Docker) that 
    analyzes the output of `mpiP` and generates a graph summarizing 
    MPI statistics. To see an example of how the notebook looks see 
    [here](https://github.com/popperized/popper-readthedocs-examples/blob/master/pipelines/mpip/results/notebook.ipynb).

The pipeline is available on github at [this
repository](https://github.com/popperized/popper-readthedocs-examples/master/pipelines/mpip).

## Results Validation

### Codifying validation of results

**TODO**

### Parameterization and parameter sweeps using Bash

**TODO**

### Continuous Validation (CI Setup)

By following a convention for structuring the files of a project, an 
experimentation pipeline execution and validation can be automated 
without the need for manual intervention. In addition to this, the 
status of a pipeline (integrity over time) can be tracked by a 
[continuous integration (CI) 
service](https://en.wikipedia.org/wiki/Comparison_of_continuous_integration_software). 
In this section we describe how Popper integrates with some existing 
CI services.

The [PopperCLI](https://github.com/systemslab/popper/popper) tool 
includes a `ci` subcommand that can be executed to generate 
configuration files for multiple CI systems. The syntax of this 
command is the following:

```bash
popper ci <system-name>
```

Where `<system-name>` is the name of CI system (see `popper ci --help` 
to get a list of supported systems). In the following, we show how to 
link github with some of the supported CI systems.

#### TravisCI

For this, we need an account at [Travis CI](http://travis-ci.org). 
Assuming our Popperized repository is already on GitHub, we can enable 
it on TravisCI so that it is continuously validated (see 
[here](https://docs.travis-ci.com/user/getting-started/) for a guide). 
Once the project is registered on Travis, we proceed to generate a 
`.travis.yml` file:

```bash
cd my-popper-repo/
popper ci travis
```

And commit the file:

```bash
git add .travis.yml
git commit -m 'Adds TravisCI config file'
```

We then can trigger an execution by pushing to GitHub:

```bash
git push
```

After this, one go to the TravisCI website to see your pipelines being 
executed. Every new change committed to a public repository will 
trigger an execution of your pipelines. To avoid triggering an 
execution for a commit, include a line with `[skip ci]` as part of the 
commit message.

> **NOTE**: TravisCI has a limit of 2 hours, after which the test is 
> terminated and failed.

#### CircleCI

For [CircleCI](https://circleci.com/), the procedure is similar to 
what we do for TravisCI (see above):

 1. Sign in to CircleCI using your github account and enable your 
    repository.

 2. Generate config files and add them to the repo:

    ```bash
    cd my-popper-repo/
    popper ci circleci
    git add .circleci
    git commit -m 'Adds CircleCI config file'
    git push
    ```

#### Jenkins

For [Jenkins](https://jenkinsci.org), generating a `Jenkinsfile` is 
done in a similar way:

```bash
cd my-popper-repo/
popper ci jenkins
git add Jenkinsfile
git commit -m 'Adds Jenkinsfile'
git push
```

Jenkins is a self-hosted service and needs to be properly configured 
in order to be able to read a github project with a `Jenkinsfile` in 
it. The easiest way to add a new project is to use the [Blue Ocean 
UI](https://jenkins.io/projects/blueocean/). A step-by-step guide on 
how to create a new project using the Blue Ocean UI can be found 
[here](https://jenkins.io/doc/book/blueocean/creating-pipelines/). In 
particular, the `New Pipeline from a Single Repository` has to be 
selected (as opposed to `Auto-discover Pipelines`).

As part of our efforts, we provide a ready-to-use Docker image for 
Jenkins with all the required dependencies. See [here](./jenkins.md) 
for an example of how to use it. We also host an instance of this 
image at <http://ci.falsifiable.us> and can provide accounts for users 
to make use of this Jenkins server (for an account, send an email to 
<ivo@cs.ucsc.edu>).

##### Jenkins Docker Image

We have created an image with all the plugins necessary to 
automatically validate Popper pipelines. To launch an instance of this 
Docker image server:

```bash
docker run -d --name=jenkins \
  -p 8080:8080 \
  -v jenkins_home:/var/jenkins_home \
  falsifiable/jenkins
```

The above launches a Jenkins server that can be accessed on port 
`8080` of the machine where this command was launched (e.g. 
`localhost:8080` if you did this on your machine).

For more info on how to use this image, take a look at the [official 
documentation](https://github.com/jenkinsci/docker/blob/master/README.md) 
for this image.

##### [`ci.falsifiable.us`](http://ci.falsifiable.us)

To make use of our server, please first send a message to 
<ivo@cs.ucsc.edu> to request an account. After an account is created, 
you will be able to access the server. Follow the steps [outlined 
here](http://popper.readthedocs.io/en/latest/ci/popperci.html#jenkins) 
to add a `Jenkinsfile` to your project. Alternatively, create this 
file manually with the following contents:

```
stage ('Popper') {
  node {
    sh "curl -O https://raw.githubusercontent.com/systemslab/popper/master/popper/_check/check.py"
    sh "chmod 755 check.py"
    sh "./check.py"
  }
}
```

Then, follow [this step-by-step 
guide](https://jenkins.io/doc/book/blueocean/creating-pipelines/) on 
how to create a new project using the Blue Ocean UI.

### Artifact evaluation criteria

The following provides a list of steps with the goal of reviewing a 
popper pipeline that someone else has created:

 1. The `popper workflow` command generates a graph that gives a 
    high-level view of what the pipeline does.

 2. Inspect the content of each of the scripts from the pipeline.

 3. Test that the pipeline works on your machine by running `popper 
    run`.

 4. Check that the git repo was archived (snapshotted) to zenodo or 
    figshare by running `popper zenodo` or `popper figshare`.

**TODO**
