# Other Resources

## CI Setup

By following a convention for structuring the files of a project, an 
experimentation pipeline execution and validation can be automated 
without the need for manual intervention. In addition to this, the 
status of a pipeline (integrity over time) can be tracked by a 
[continuous integration (CI) 
service](https://en.wikipedia.org/wiki/Comparison_of_continuous_integration_software). 
In this section we describe how to generate configuration files and 
how to setup a CI service so that it continously validate the 
integrity of a pipeline.

The `popper` command includes `ci` subcommand that can be executed to 
generate configuration files for multiple CI systems. The syntax of 
this command is the following:

```bash
popper ci --service <name>
```

Where `<name>` is the name of CI system (see `popper ci --help` to get 
a list of supported systems). In the following, we show how to link 
github with some of the supported CI systems. In order to do so, we 
first need to create a repository on github and upload our commits:

```bash
# set the new remote
git remote add origin <your-github-repo-url>

# verify the remote URL
git remote -v

# push changes in your local repository up to github
git push -u origin master
```

### TravisCI

For this, we need an account at [Travis CI](http://travis-ci.org). 
Assuming our Popperized repository is already on GitHub, we can enable 
it on TravisCI so that it is continuously validated (see 
[here](https://docs.travis-ci.com/user/getting-started/) for a guide). 
Once the project is registered on Travis, we proceed to generate a 
`.travis.yml` file:

```bash
cd my-popper-repo/
popper ci --service travis
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

### CircleCI

For [CircleCI](https://circleci.com/), the procedure is similar to 
what we do for TravisCI (see above):

 1. Sign in to CircleCI using your github account and enable your 
    repository.

 2. Generate config files and add them to the repo:

    ```bash
    cd my-popper-repo/
    popper ci --service circle
    git add .circleci
    git commit -m 'Adds CircleCI config files'
    git push
    ```

### Jenkins

For [Jenkins](https://jenkinsci.org), generating a `Jenkinsfile` is 
done in a similar way:

```bash
cd my-popper-repo/
popper ci --service jenkins
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
Jenkins with all the required dependencies (see below) for an example 
of how to use it. We also host an instance of this image at 
<http://ci.falsifiable.us> and allow anyone to make use of this 
Jenkins server.

#### Jenkins Docker Image

We have created an image with all the plugins necessary to 
automatically validate pipelines. To launch an instance of this Docker 
image server:

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

#### [`ci.falsifiable.us`](http://ci.falsifiable.us)

Create an account by clicking the `Sign Up` link on the top right 
corner. After this, you will be able to access the server. Follow the 
steps outlined above to generate a `Jenkinsfile` using the `popper` 
command. Alternatively, create this file manually with the following 
contents:

```
stage ('Popper') {
  node {
    sh "git clone --recursive https://github.com/systemslab/popper /tmp/popper"
    sh "export PATH=$PATH:/tmp/popper/cli/bin"
    sh "export PYTHONUNBUFFERED=1"
  }
}
```

Then, follow [this step-by-step 
guide](https://jenkins.io/doc/book/blueocean/creating-pipelines/) on 
how to create a new project using the Blue Ocean UI.

## Automated Artifact Evaluation

A growing number of Computer Science conferences and journals 
incorporate an artifact evaluation process in which authors of 
articles submit [artifact 
descriptions](http://ctuning.org/ae/submission.html) that are tested 
by a committee, in order to verify that experiments presented in a 
paper can be re-executed by others. In short, an artifact description 
is a 2-3 page narrative on how to replicate results, including steps 
that detail how to install software and how to re-execute experiments 
and analysis contained in a paper.

An alternative to the manual creation and verification of an Artifact 
Description (AD) is to use a continuous integration (CI) service such 
as GitLab-CI or Jenkins. Authors can make use of a CI service to 
automate the experimentation pipelines associated to a paper. By doing 
this, the URL pointing to the project on the CI server that holds 
execution logs, as well as the repository containing all the 
automation scripts, can serve as the AD. In other words, the 
repository containing the code for experimentation pipelines, and the 
associated CI project, serve both as a "self-verifiable AD". Thus, 
instead of requiring manually created ADs, conferences and journals 
can request that authors submit a link to a code repository (Github, 
Gitlab, etc.) where automation scripts reside, along with a link to 
the CI server that executes the pipelines.

While automating the execution of a pipeline can be done in many ways, 
in order for this approach to serve as an alternative to ADs, there 
are five high-level tasks that pipelines must carry out in every 
execution:

  * Code and data dependencies. Code must reside on a version control 
    system (e.g. github, gitlab, etc.). If datasets are used, then 
    they should reside in a dataset management system (datapackage, 
    gitlfs, dataverse, etc.). The experimentation pipelines must 
    obtain the code/data from these services on every execution.
  * Setup. The pipeline should build and deploy the code under test. 
    For example, if a pipeline is using containers or VMs to package 
    their code, the pipeline should build the container/VM images 
    prior to executing them. The goal of this is to verify that all 
    the code and 3rd party dependencies are available at the time a 
    pipeline runs, as well as the instructions on how to build the 
    software.
  * Resource allocation. If a pipeline requires a cluster or custom 
    hardware to reproduce results, resource allocation must be done as 
    part of the execution of the pipeline. This allocation can be 
    static or dynamic. For example, if an experiment runs on custom 
    hardware, the pipeline can statically allocate (i.e. hardcode 
    IP/hostnames) the machines where the code under study runs (e.g. 
    GPU/FPGA nodes). Alternatively, a pipeline can dynamically 
    allocate nodes (using infrastructure automation tools) on 
    CloudLab, Chameleon, Grid5k, SLURM, Terraform (EC2, GCE, etc.), 
    etc.
  * Environment capture. Capture information about the runtime 
    environment. For example, hardware description, OS, system 
    packages (i.e. software installed by system administrators), 
    remote services (e.g. a scheduler). Many open-source tools can aid 
    in aggregating this information such as SOSReport or facter.
  * Validation. Scripts must verify that the output corroborates the 
    claims made on the article. For example, the pipeline might check 
    that the throughput of a system is within an expected confidence 
    interval (e.g. defined with respect to a baseline obtained at 
    runtime).

A list of example Popper pipelines meeting the above criteria:

  * [BLIS 
    paper](https://github.com/popperized/popper-readthedocs-examples/tree/master/pipelines/blis). 
    We took an appendix and turned it into executable pipeline.
  * [HPC Proxy 
    App](https://github.com/popperized/popper-readthedocs-examples/tree/master/pipelines/mpip). 
    Runs LULESH linked against MPIp to capture runtime MPI perf 
    metrics.
  * [Linux kernel 
    development](https://github.com/popperized/popper-readthedocs-examples/tree/master/pipelines/linux-cgroups). 
    Uses a VM to compile, test and deploy Linux.
  * [Relational database 
    performance](https://github.com/popperized/popper-readthedocs-examples/tree/master/pipelines/pgbench). 
    Runs pgbench to compare two versions of postgres.

More examples are listed 
[here](https://popper.rtfd.io/en/latest/sections/examples.html).

> **NOTE**: A pipeline can be implemented by any means and does 
> **not** need to be implemented using the Popper CLI. While the 
> examples we link above are of Popper pipelines, this subsection has 
> the intention to apply, in general, to any type of automated 
> approach. Our intention is to define, in written form, the criteria 
> for Automated Artifact Evaluation.

### CI Infrastructure for Automated Artifact Evaluation

We have an instance of Jenkins running at <http://ci.falsifiable.us>, 
maintained by members of the Systems Research Lab (SRL) at UC Santa 
Cruz. Detailed instructions on how to create an account on this 
service and how to use it is available 
[here](https://popper.readthedocs.io/en/latest/ci/jenkins.html) (also 
includes instructions on how to self-host it). This service allows 
researchers and students to automate the execution and validation of 
experimentation pipelines without happing to deploy infrastructure of 
their own.

## Self-paced Tutorial

A hands-on, self-paced tutorial is available 
[here](https://popperized.github.io/swc-lesson).

