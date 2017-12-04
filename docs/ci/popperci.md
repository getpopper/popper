# Popper and CI systems

By following a convention for structuring the files of a project, 
experiment execution and validation can be automated without the need 
for manual intervention. In addition to this, the status of an 
experiment (integrity over time) can be tracked by a CI service. In 
this section we describe the workflow that one follows in order to 
make an experiment suitable for automation on CI systems.

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
|-- teardown.sh
```

Every experiment has `setup.sh`, `run.sh` and `validate.sh` scripts 
that serve as the interface to the experiment. All these return 
non-zero exit codes if there's a failure. In the case of 
`validate.sh`, this script should print to standard output one line 
per validation, denoting whether a validation passed or not. In 
general, the form for validation results is `[true|false] <statement>` 
(see examples below).

```{#lst:validations .bash caption="Example output of validations."}
[true]  algorithm A outperforms B
[false] network throughput is 2x the IO bandwidth
```

The [PopperCLI](https://github.com/systemslab/popper/popper) tool 
includes an `experiment init` subcommand that can be executed to 
scaffold an experiment with the above structure. The syntax of this 
command is the following:

```bash
popper experiment init <name>
```

Where `<name>` is the name of the experiment to initialize.

## CI System Configuration

In this section we describe how to configure a CI system so that 
Popper experiments can be continuously validated. The next section 
describes the multiple steps that are executed as part of this 
validation process.

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

### Travis CI

For this, we need an account at [Travis CI](http://travis-ci.org). 
Assuming our Popperized repository is already on GitHub, we can enable 
it on the TravisCI so that it is continuously validated (see 
[here](https://docs.travis-ci.com/user/getting-started/) for a guide). 
Once the project is registered on Travis, we procceed to generate 
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

After this, one can go to the TravisCI website to see your experiments 
being executed.

## CI Functionality

The following is the list of steps that are verified when validating 
an experiment:

<!--

 1. Ensure that every versioned dependency is healthy. For example, 
    ensure that external repos can be cloned correctly.
 2. Check the integrity of every special subfolder (see previous 
    subsection).
-->

 1. For every experiment, trigger an execution (invoke `setup.sh` 
    followed by `run.sh`).
 2. After the experiment finishes, execute validations on the output 
    (invoke `validate.sh`).
 3. Keep track of every experiment and report their status.
 4. Execute `teardown.sh`

There are three possible statuses for every experiment: `FAIL`, `PASS` 
and `GOLD`. There are two possible values for the status of a 
validation, `FAIL` or `PASS`. When the experiment status is `FAIL`, 
this list of validations is empty since the experiment execution has 
failed and validations are not able to execute at all. When the 
experiment status' is `GOLD`, the status of all validations is `PASS`. 
When the experiment runs correctly but one or more validations fail 
(experiment's status is `PASS`), the status of one or more validations 
is `FAIL`.

## Popper Badges

We maintain a badging service that can be used to keep track of the 
status of an experiment. In order to enable this, the 
`--enable-badging` flag has to be passed to the `popper ci` 
subcommand.

![Badging service.](/figures/cibadges.png)

Badges are commonly used to denote the status of a software project 
with respect to certain aspect, e.g. whether the latest version can be 
built without errors, or the percentage of code that unit tests cover 
(code coverage). Badges available for Popper are shown in the above 
figure. If badging is enabled, after the execution of an experiment, 
the status of an experiment is recorded in the badging server, which 
keeps track of statuses for every revision of every experiment.

Users can include a link to the badge in the `README` page of an 
experiment, which can be displayed on the web interface of the version 
control system (GitHub in this case). The CLI tool can generate links 
for experiments:

```bash
popper badge <exp>
```

Which prints to `stdout` the text that should be added to the `README` 
file of the experiment.

## Testing Locally

The 
[PopperCLI](https://github.com/systemslab/popper/tree/master/popper) 
tool includes a `check` subcommand that can be executed to test 
locally. This subcommand is the same that is executed by the PopperCI 
service, so the output of its invocation should be, in most cases, the 
same as the one obtained when PopperCI executes it. This helps in 
cases where one is testing locally. To execute test locally:

```bash
cd my/paper/repo
popper check myexperiment

Popper check started
Running stage setup.sh ....
Running stage run.sh ................
Running stage validate.sh .
Running stage teardown.sh ..
Popper check finished: SUCCESS
```

The status of the execution is stored in the `popper_status` file, 
while `stdout` and `stderr` output for each stage is written to the 
`popper_logs` folder.

```bash
tree popper_logs
popper_logs/
├── run.sh.out
├── run.sh.err
├── setup.sh.out
├── setup.sh.err
├── teardown.sh.out
├── teardown.sh.err
├── validate.sh.out
└── validate.sh.err
```
