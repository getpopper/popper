Following the Popper convention results in producing self-contained 
experiments and articles, and reduces significantly the amount of work 
that a reviewer or reader has to undergo in order to re-execute 
experiments. However, it still requires manual effort in order to 
re-execute an experiment. For experiments that can run locally where 
the Popper repository is checked out (e.g. not sensitive to 
variability of underlying hardware), this is not an issue since 
usually an experiment is executed by typing a couple of commands to 
re-execute and validate an experiment. In the case of experiments that 
need to be executed remotely (e.g. dedicated hardware), this is not as 
straight-forward since there is a significant amount of effort 
involved in requesting and configuring infrastructure.

The idea behind PopperCI is simple: by structuring a project in a 
commonly agreed way, experiment execution and validation can be 
automated without the need for manual intervention. In addition to 
this, the status of an experiment (integrity over time) can be tracked 
by the service hosted at ci.falsifiable.us. In this section we 
describe the workflow that one follows in order to make an experiment 
suitable for automation on the PopperCI service. In the next section, 
we show a use case that illustrates the usage with a concrete example.

## Experiment Folder Structure

A minimal experiment folder structure for an experiment is shown 
below:

```{#lst:repo .bash caption="Basic structure of a Popper repository."}
$> tree -a paper-repo/experiments/myexp
paper-repo/experiments/myexp/
|-- README.md
|-- .popper.yml
|-- run.sh
|-- setup.sh
|-- validate.sh
```

Every experiment has `setup.sh`, `run.sh` and `validate.sh` scripts 
that serve as the interface to the experiment. All these return 
non-zero exit codes if there's a failure. In the case of 
`validate.sh`, this script should print to standard output one line 
per validation, denoting whether a validation passed or not. In 
general, the form for validation results is `[true|false] 
<statement>`. Examples are shown in @Lst:validations.

```{#lst:validations .bash caption="Example output of validations."}
[true]  algorithm A outperforms B
[false] network throughput is 2x the IO bandwidth
```

## Special Subfolders

Folders named after a tool (e.g. `docker` or `terraform`) have special 
meaning. For each of these, tests are executed that check the 
integrity of the associated files. For example, if we have an 
experiment that is orchestrated with [Ansible](http://ansible.com), 
the associated files are stored in an `ansible` folder. When checking 
the integrity of this experiment, the `ansible` folder is inspected 
and associated files are checked to see if they are healthy. The 
following is a list of currently supported folder names and their CI 
semantics (support for others is in the making):

  * `docker`. An image is created for every `Dockerfile`.
  * `ansible`. YAML syntax is checked.
  * `datapackages`. Availability of every dataset is checked.
  * `vagrant`. Definition of the VM is verified.
  * `terraform`. Infrastructure configuration files are checked by 
    running `terraform validate`.
  * `geni`. Test using the `omni validate` command.

By default, when a check invokes the corresponding tool, PopperCI uses 
the latest stable version. If another version is required, users can 
add a `.popper.yml` file to specify this.

## CI Functionality

Assuming users have created an account at the PopperCI website and 
installed a git hook in their local repository, after a new commit is 
pushed to the repository that stores the experiments, the service goes 
over the following steps:

 1. Ensure that every versioned dependency is healthy. For example, 
    ensure that external repos can be cloned correctly.
 2. Check the integrity of every special subfolder (see previous 
    subsection).
 3. For every experiment, trigger an execution (invokes `run.sh`), 
    possibly launching the experiment on remote infrastructure (see 
    next section).
 4. After the experiment finishes, execute validations on the output 
    (invoke `validate.sh` command).
 5. Keep track of every experiment and report their status.

Once an experiment has been successfully validated by PopperCI, it 
becomes push-button repeatable. If an experiment has been made public, 
other users can re-execute it instantly, assuming they have an account 
at the PopperCI website with the appropriate credentials on the 
platform where the experiment originally executed (e.g. authentication 
certificates for CloudLab).

## Experiment Execution

![PopperCI dashboard showing the status of every experiment for every 
commit.
](figures/popperci_dashboard_experiments.png){#fig:experiments}

Experiments that run on remote infrastructure specify any preparation 
tasks in the `setup.sh` script. For example, an experiment can 
leverage [Terraform](https://terraform.io) to initialize the resources 
required to execute. In this case, an special `terraform/` folder 
contains one or more [Terraform configuration 
files](https://www.terraform.io/docs/configuration/) (JSON-compatible, 
declarative format) that specify the infrastructure that needs to be 
instantiated in order for the experiment to execute. The `run.sh` 
script assumes that there is a `terraform.tfstate` folder that 
contains the output of the `terraform apply` command. For example, 
this folder contains information about whether all the nodes in an 
experiment have initialized correctly.

Terraform is a generic tool that initializes infrastructure in a 
platform-agnostic way by interposing an abstraction layer that is 
implemented using platform-specific tools. When a plugin for a 
particular infrastructure is not available, one can resort to using 
platform-specific tools directly. For example CloudLab 
[@ricci_introducing_2014] and Grid500K [@bolze_grid5000_2006] have a 
set of CLI tools that can be used to manage the request of 
infrastructure. In general, any tool that fits in this category that 
has a command line interface (CLI) tool available can be used to 
automate this process.

## PopperCI Dashboard

The PopperCI website, once users have logged in, shows the status of 
the experiments for their projects. For each project, there is a table 
that shows the status of every experiment, for every commit 
(@Fig:experiments).

There are three possible statuses for every experiment: `FAIL`, `PASS` 
and `GOLD`. Clicking an entry on the above table shows a `validations` 
sub-table with two columns, `validation` and `status`, that shows the 
status for every validation. There are two possible values for the 
status of a validation, `FAIL` or `PASS`. When the experiment status 
is `FAIL`, this list is empty since the experiment execution has 
failed and validations are not able to execute at all. When the 
experiment status is `GOLD`, the status of all validations is `PASS`. 
When the experiment runs correctly but one or more validations fail 
(experiment's status is `PASS`), the status of one or more validations 
is `FAIL`.

PopperCI has a badge service that projects can include in the `README` 
page of a project on the web interface of the version control system 
(e.g. GitHub). Badges are commonly used to denote the status of a 
software project, e.g. whether the latest version can be built without 
errors, or the percentage of code that unit tests cover (code 
coverage). Badges available for Popper are shown in @Fig:popperci 
(step 6).
