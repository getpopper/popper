# CLI feautures

## New pipeline initialization

**TODO**

## Searching and importing existing pipelines

**TODO**

## Executing a pipeline

**TODO**

## Continously validating a pipeline

The following is the list of steps that are verified when validating 
an pipeline:

 1. For every pipeline, trigger an execution by sequentially invoking 
    all the scripts for all the defined stages of the pipeline.
 2. After the pipeline finishes, if a `validate.sh` script is defined, 
    parse its output.
 3. Keep track of every pipeline and report their status.

There are three possible statuses for every pipeline: `FAIL`, `PASS` 
and `GOLD`. There are two possible values for the status of a 
validation, `true` or `false`. When the pipeline status is `FAIL`, this 
list of validations is empty since the pipeline execution has failed 
and validations are not able to execute at all. When the pipeline 
status' is `GOLD`, the status of all validations is `true`. When the 
pipeline runs correctly but one or more validations fail (pipeline's 
status is `PASS`), the status of one or more validations is `false`.

### Testing Locally

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

These files are added to the 
[`.gitignore`](https://help.github.com/articles/ignoring-files/) file 
so they won't be committed to the git repository when doing `git add`. 
To quickly remove them, one can clean the working tree:

```bash
# get list of files that would be deleted
# include directories (-d)
# include ignored files (-x)
git clean -dx --dry-run

# remove --dry-run and add --force to actually delete files
git clean -dx --force
```

### Testing Remotely via a CI service

This is explained 
[here](examples.html#continuous-validation-ci-setup).

### Popper Badges

We maintain a badging service that can be used to keep track of the 
status of a pipeline. In order to enable this, the `--enable-badging` 
flag has to be passed to the `popper ci` subcommand.

![Badging service.](/figures/cibadges.png)

Badges are commonly used to denote the status of a software project 
with respect to certain aspect, e.g. whether the latest version can be 
built without errors, or the percentage of code that unit tests cover 
(code coverage). Badges available for Popper are shown in the above 
figure. If badging is enabled, after the execution of a pipeline, the 
status of a pipeline is recorded in the badging server, which keeps 
track of statuses for every revision of ever pipeline.

Users can include a link to the badge in the `README` page of a 
pipeline, which can be displayed on the web interface of the version 
control system (GitHub in this case). The CLI tool can generate links 
for pipelines:

```bash
popper badge <exp>
```

Which prints to `stdout` the text that should be added to the `README` 
file of the pipeline.


## Visualizing a pipeline

**TODO**

## Adding metadata to a project

**TODO**

## Archiving a project and obtaining DOIs

**TODO**

## Popper Badges

**TODO**

## The `popper.yml` configuration file

The `popper` command reads the `.popper.yml` file in the root of a 
project to figure out how to execute pipelines. While this file can be 
manually created and modified, the `popper` command makes changes to 
this file depending on which commands are executed.

The project folder we will use as example looks like the following:

```
$> tree -a -L 2 my-paper
my-paper/
├── .git
├── .popper.yml
├── paper
└── pipelines
    ├── analysis
    └── data-generation
```

That is, it contains three pipelines named `data-generation` and `analysis`. The `.popper.yml` for this project looks 
like:

```yaml

pipelines:
  paper:
    envs:
    - host
    path: paper
    stages:
    - build
  data-generation:
    envs:
    - host
    path: pipelines/data-generation
    stages:
    - first
    - second
    - post-run
    - validate
    - teardown
  analysis:
    envs:
    - host
    path: pipelines/analysis
    stages:
    - run
    - post-run
    - validate
    - teardown

metadata:
  author: My Name
  name: The name of my study

popperized:
  - github/popperized
  - github/ivotron/quiho-popper
```

At the top-level of the YAML file there are entries named `pipelines`, `metadata` and 
`popperized`.

### Pipelines

The `pipelines` YAML entry specifies the details for all the available
pipelines. For each pipeline, there is information about:

   *  the environment(s) in which the pipeline is be executed.
   *  the path to that pipeline.
   *  the various stages that are present in it.

The special `paper` pipeline is generated by executing `popper 
init paper` and has by default a single stage named `build.sh`.

#### `envs`

The `envs` entry in `.popper.yml` specifies the environment that a 
pipeline is used when the pipeline is executed as part of the `popper 
run` command. The available environments are:

  * `host`. The experiment is executed directly on the host.
  * `alpine-3.4`, `ubuntu-16.04` and `centos-7.2`. For each of these, 
    `popper check` is executed within a docker container whose base 
    image is the given Linux distribution name. The container has 
    `docker` available inside it so other containers can be executed 
    from within the `popper check` container.

The `popper init` command can be used to initialize a pipeline. By 
default, the `host` is registered when using `popper init`. The 
`--env` flag of `popper init` can be used to specify another 
environment. For example:

```bash
popper init mypipe --env=alpine-3.4
```

The above specifies that the pipeline named `mypipe` will be executed 
inside a docker container using the `alpine-3.4` popper check image.

To add more environment(s):  

```bash
popper env myexp --add ubuntu-xenial,centos-7.2
```

To remove enviroment(s):  

```bash
popper env myexp --rm centos-7.2
```

#### `stages`

The `stages` YAML entry specifies the sequence of stages that are 
executed by the `popper run` command. By default, the `popper init` 
command generates scaffold scripts for `setup.sh`, `run.sh`, 
`post-run.sh`, `validate.sh`, `teardown.sh`. If any of those are not
present when the pipeline is executed using `popper run`, they are 
just skipped (without throwing an error). At least one stage needs to
be executed, otherwise `popper run` throws an error.

If arbitrary names are desired for a pipeline, the `--stages` flag of 
the `popper init` command can be used. For example:

```bash
popper init arbitrary_stages \
  --stages 'preparation,execution,validation' \
```

The above line generates the configuration for the `arbitrary_stages` 
pipeline showed in the example.

### Metadata

The `metadata` YAML entry specifies the set of data that gives information
about the user's project. It can be added using the `popper metadata --add command`
For example :

```bash
popper metadata --add authors='Dennis Ritchie'
```

This adds a metadata entry 'authors' to the the project
metadata.

To view the `metadata` of a repository type: 

```bash
popper metadata
```
To remove the entry 'authors' from the `metadata`:

```bash
popper metadata --rm authors
```

### Popperized repositories catalog

The `popperized` YAML entry specifies the list of Github organizations and repositories that contain popperized pipelines. By default, it points to the 
`github/popperized` organization. This list is used to look for pipelines as part of the `popper search` command.
