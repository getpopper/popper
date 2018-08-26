# Other Resources

## Automated Artifact Evaluation

A growing number of CS conferences and journals incorporate an 
artifact evaluation process in which authors of articles submit 
[artifact descriptions](http://ctuning.org/ae/submission.html) that 
are tested by a committee, in order to verify that experiments 
presented in a paper can be re-executed by others. In short, an 
artifact description is a 2-3 page narrative on how to replicate 
results, including steps that detail how to install software and how 
to re-execute experiments and analysis contained in a paper.

An alternative to the manual creation of an Artifact Description (AD) 
is to use a continuous integration (CI) service such as GitLab-CI or 
Jenkins. Authors can make use of a CI service to automate the 
experimentation pipelines associated to a paper. By doing this, the 
URL pointing to the project on the CI server that holds execution 
logs, as well as the repository containing all the automation scripts 
can serve as the AD. In other words, the repository containing the 
code for experimentation pipelines, and the associated CI project, 
serve both as an "executable AD". Thus, instead of requiring ADs, 
conferences and journals can request that authors submit a link to a 
code repository (Github, Gitlab, etc.) where automation scripts 
reside, along with a link to the CI server that executes the 
pipelines.

While automating the execution of a pipeline can be done in many ways, 
in order for this approach to serve as an alternative to ADs, there 
are four high-level tasks that pipelines must carry out in every 
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

More examples are listed [here](examples.html).

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

