# CLI feautures

## New pipeline initialization

Create a Git repository:

```bash
mkdir mypaper
cd mypaper
git init
echo '# mypaper' > README.md
git add .
git commit -m 'first commit'
```

Initialize the popper repository and add the configuration file to git:

```bash
popper init
git add .
git commit -m 'adds .popper.yml file'
```

Initialize pipeline using `init` (scaffolding):

```bash
popper init myexp
```

Show what this did:

```bash
ls -l pipelines/myexp
```

Commit the "empty" pipeline:

```bash
git add pipelines/myexp
git commit -m 'adding myexp scaffold'
```

## Executing a pipeline

To automatically run a pipeline:

```bash
popper run myexp
```

or to execute all the pipelines in a project:

```bash
popper run
```

Once a pipeline is run, one can show the logs:

```bash
ls -l pipelines/myexp/popper/host
```

## Reusing existing pipelines

Many times, when starting an experiment, it is useful to be able to use
existing pipelines as scaffolding for the operations we wish to make. The
[Popperized](https://github.com/popperized) GitHub organization exists as a
curated list of existing Popperized experiments and examples, for the purpose
of both learning and scaffolding new projects. Additionally, the CLI includes
capabilities easily sift through and import these pipelines.


### Searching for existing pipelines

The Popper CLI is capable of searching for premade and template pipelines that
you can modify for your own uses. You can use the `popper search` command to
find pipelines using keywords. For example, to search for pipelines that use
docker you can simply run:

```bash
$ popper search docker
[####################################] Searching in popperized | 100%

Search results:

> popperized/popper-readthedocs-examples/docker-data-science

> popperized/swc-lesson-pipelines/docker-data-science
```

By default, this command will look inside the
[Popperized](https://github.com/popperized) GitHub organization but you
can configure it to search the GitHub organization or repository of your choice
using the `popper search --add <org-or-repo-name>` command. If you've added
more organizations, you may list them with `popper search --ls`, or remove one
with `popper search --rm <org-or-repo-name>

Additionally, when searching for a pipeline, you may choose to include the
contents of the readme in your search if you wish by providing the additional
`--include` flag to `popper search`.


### Importing existing pipelines

Once you have found a pipeline you're interested in importing, you can use
`popper add` plus the full pipeline name to add the pipeline to the popperized
project:

```bash
$ popper add popperized/popper-readthedocs-examples/docker-data-science
Downloading pipeline docker-data-science as docker-data-science...
Updating popper configuration...
Pipeline docker-data-science has been added successfully.
```

This will download the contents of the repo to your project tree and register
it in your `.popper.yml` configuration file. If you want to add the pipeline
inside a different folder, you can also specify that in the `popper add`
command:

```bash
$ popper add popperized/popper-readthedocs-examples/docker-data-science docker-pipeline
Downloading pipeline docker-data-science as docker-pipeline...
Updating popper configuration...
Pipeline docker-pipeline has been added successfully.

$ tree
mypaper
└── pipelines
    └── docker-pipeline
        ├── README.md
        ├── analyze.sh
        ├── docker
        │   ├── Dockerfile
        │   ├── app.py
        │   ├── generate_figures.py
        │   └── requirements.txt
        ├── generate-figures.sh
        ├── results
        │   ├── naive_bayes.png
        │   ├── naive_bayes_results.csv
        │   ├── svm_estimator.png
        │   └── svm_estimator_results.csv
        └── setup.sh

```

You can also tell `popper add` to instead pull the pipeline from another git
branch by optionally providing the `--branch <branch-name>` option to the
command.


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
tool includes a `run` subcommand that can be executed to test
locally. This subcommand is the same that is executed by the PopperCI
service, so the output of its invocation should be, in most cases, the
same as the one obtained when PopperCI executes it. This helps in
cases where one is testing locally. To execute test locally:

```bash
cd my/paper/repo
popper run myexperiment

[####################################] None

status: SUCCESS
```

The status of the execution, as well as the `stdout` and `stderr` output for
each stage is stored in the `popper/host` directory inside your pipeline. In
addition to the `host` directory, a new directory will be created for every
environment you set your pipeline to run on.

```bash
popper/host
├── popper_status
├── post-run.sh.err
├── post-run.sh.out
├── run.sh.err
├── run.sh.out
├── setup.sh.err
├── setup.sh.out
├── teardown.sh.err
├── teardown.sh.out
├── validate.sh.err
└── validate.sh.out
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

#### Execution timeout

By default, `popper run` will set a timeout on the execution of your
pipelines. You may modify the timeout using the `--timeout` option,
in the form of `popper run --timeout 600s`. You can also disable
the timeout altogether by setting `--timeout` to 0.


### Testing Remotely via a CI service

This is explained [here](./other_resources.html#ci-setup).

## Popper Badges

We maintain a badging service that can be used to keep track of the
status of a pipeline.

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
popper badge --service popper
```

Which prints to `stdout` the text that should be added to the `README`
file of the pipeline.

## Visualizing a pipeline

Popper gives a user the ability to visualize the workflow of a pipeline using the
`popper workflow pipeline_name` command. The command generates a workflow diagram
corresponding to a Popper pipeline, in the .dot format. The string defining
the graph is printed to stdout so it can be piped into other tools.
For example,to generate a png file, one can make use of the graphviz CLI tools:

```bash
popper workflow mypipe | dot -T png -o mypipe.png.
```

Suppose you want to visualize the [co2-emissions](https://github.com/popperized/swc-lesson-pipelines/tree/master/pipelines/co2-emissions) pipeline.
Assuming that this pipeline is added to your repository (as explained ini
[Searching and Importing pipelines](cli_features.html#searching-and-importing-existing-pipelines),
you need to type:

```bash
popper workflow co2-emissions | dot -T png -o co2_workflow.png
```

This will lead to the generation of the following dot graph:

![](/figures/example_co2_workflow.png)


## Adding metadata to a project

Metadata to a project can be added using the `metadata` command, which
adds a `key-value` pair to the repository (to the `.popper.yml` file).
For example:

```
popper metadata --add author='Jane Doe'
```

The above adds the metadata item `author` to the project. To retrieve
the list of keys:

```bash
popper metadata
```

And one removes a key by doing:

```bash
popper metadata --rm author
```


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

That is, it contains three pipelines named `paper`,`data-generation` and `analysis`. The `.popper.yml` for this project
looks like:

```yaml

metadata:
  access_right: open
  license: CC-BY-4.0
  publication_type: article
  upload_type: publication

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

popperized:
  - github/popperized
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

The `envs` entry in `.popper.yml` specifies the environment in which a
pipeline is executed as part of the `popper run` command. The available
environments are:

  * `host`. The experiment is executed directly on the host.
  * `alpine-3.4`, `ubuntu-16.04` and `centos-7.2`. For each of these,
    `popper run` is executed within a docker container whose base
    image is the given Linux distribution name. The container has
    `docker` available inside it so other containers can be executed
    from within the `popper run` container.

The `popper init` command can be used to initialize a pipeline. By
default, the `host` is the registered environment when using `popper init`.
The `--env` flag of `popper init` can be used to specify another
environment. For example:

```bash
popper init mypipe --env=alpine-3.4
```

The above specifies that the pipeline named `mypipe` will be executed
inside a docker container using the `alpine-3.4` popper check image.

To add more environment(s):  

```bash
popper env mypipe --add ubuntu-xenial,centos-7.2
```

To remove an enviroment from the pipeline:  

```bash
popper env mypipe --rm centos-7.2
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

The `metadata` YAML entry specifies a set of key-value pairs that
describes and gives us information about a project.

By default, a project's metadata will be initialized with the
following key-value pairs:

```
$> popper metadata

access_right: open
license: CC-BY-4.0
publication_type: article
upload_type: publication
```

A custom key-value pair can be added using the
popper metadata --add KEY=VALUE` command.
For example:

```bash
popper metadata --add year=2018
```

This adds a metadata entry 'year' to the metadata.
The metadata will now look like:

```
access_right: open
license: CC-BY-4.0
publication_type: article
upload_type: publication
year: '2019'
```
To remove the entry 'year' from the `metadata`,
the `popper metadata --rm KEY` command can be used
as show below:

```bash
popper metadata --rm year
```

### Archiving and DOI generation

Currently Popper CLI tool integrates with services like Zenodo and FigShare
for archiving.

#### Zenodo

The first step is to create an account on Zenodo and generate an API token.
Follow these steps (copied from [here]
(http://developers.zenodo.org/#creating-a-personal-access-token)):

 1. [Register](https://zenodo.org/signup) for a Zenodo account if you
    don’t already have one.
 2. Go to your
    [Applications](https://zenodo.org/account/settings/applications/),
    to create a [new
    token](https://zenodo.org/account/settings/applications/tokens/new/).
 3. Select the OAuth scopes you need (you need at least
    `deposit:write` and `deposit:actions`).

Now add some required metadata.

```bash
popper metadata --add title='<Your Title>'
popper metadata --add author1='<First Last, first.last@gmail.com, Affiliation>'
popper metadata --add abstract='<A short description of the your repo>'
popper metadata --add keywords='<comma, separated, keywords>'
```

Now use the `popper archive` command to perform the archiving.

```bash
popper archive --service zenodo
```

Enter the token obtained when prompted and you will have a DOI available for  
your repository.

#### FigShare

Create a personal token using the following steps:

1. Go to https://figshare.com and create a new account.
2. Go to the [Applications](https://figshare.com/account/applications) section
of your profile and in the bottom click on `Create Personal Token`.
3. Keep the token safe for use in the next step.

Now add some metadata.

```bash
popper metadata --add title='Popper test archive'
popper metadata --add author1='Test Author, testauthor@gmail.com, popper'
popper metadata --add abstract='A short description of the article'
popper metadata --add keywords='comma, separated, keywords'
popper metadata --add categories='1656'
```

Now use the `popper archive` command to perform the archiving.

```bash
popper archive --service figshare
```

Enter the token obtained when prompted to complete the archival and get the DOI.

### Popperized repositories catalog

The `popperized` YAML entry specifies the list of Github organizations and repositories that contain popperized pipelines. By default, it points to the
`github/popperized` organization. This list is used to look for pipelines as part of the `popper search` command.
