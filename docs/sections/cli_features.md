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

For more on the execution logic, see 
[here](ci_features.html#execution-logic).

## Specifying environment requirements

The `require` subcommand can be used to specify expectations on the 
environment, in particular, the availability of certain environment 
variables and binary commands. To specify that a variable is required, 
the following can be done:

```
popper require --env VARIABLE_NAME
```

and for commands:

```
popper require --binary command-name
```

In either case, the `popper run` command will check, prior to 
executing a pipeline, the existence of these and will proceed 
according to the value given to the `--requirement-level` flag of the 
`run` subcommand. By default, the execution fails if a dependency is 
missing.

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
with `popper search --rm <org-or-repo-name>`

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

## Continuously validating a pipeline

The `ci` subcommand generates configuration files for multiple CI 
systems. The syntax of this command is the following:

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

### GitLab-CI

For [GitLab-CI](https://about.gitlab.com/features/gitlab-ci-cd/), the 
procedure is similar to what we do for TravisCI and CircleCI (see 
above), i.e. generate config files and add them to the repo:

```bash
cd my-popper-repo/
popper ci --service gitlab
git add .gitlab-ci.yml
git commit -m 'Adds GitLab-CI config file'
git push
```

If CI is enabled on your instance of GitLab, the above should trigger 
an execution of the pipelines in your repository.

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

As part of our efforts, we provide a ready-to-use [Docker image for 
Jenkins](jenkins.html) with all the required dependencies. We also 
host an instance of this image at <http://ci.falsifiable.us> and allow 
anyone to make use of this Jenkins server.

For more on the CI concept, see [here](). For a detailed explanation 
on all the CI features, see [here](). And for
In this case, as opposed

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

## Popper Badges

We maintain a badging service that can be used to keep track of the
status of a pipeline.

![Badging service.](/figures/cibadges.png)

Badges are commonly used to denote the status of a software project 
with respect to certain aspect, e.g. whether the latest version can be 
built without errors, or the percentage of code that unit tests cover 
(code coverage). Badges available for Popper are shown in the above 
figure. If badging is enabled, after the execution of a pipeline, the 
status of a pipeline is recorded in the badging server (hosted at 
<http://badges.falsifiable.us>), which keeps track of the status for 
every revision of a Popperized project. To retrieve the history for a 
Popper repo:

```bash
popper badge --history
```

A link to the badge can be included in the `README.md` page of a 
project, which is displayed on the web interface of the version 
control system (GitHub, GitLab, etc.). The CLI tool can generate the 
link automatically:

```bash
popper badge --service popper
```

Which prints to `stdout` the text that should be added to the 
`README.md` file of the project. If the `--inplace` flag is used, the 
link is added to the `README.md` file.

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

## Archiving and DOI generation

Currently the Popper CLI tool integrates with archival services Zenodo 
and FigShare for uploading the contents of the repository. This is 
useful for archiving data that is not part of the Git repository 
(usually due to it being too big). In addition, these services provide 
the ability of obtaining a DOI for the archive associated to the 
project.

### Zenodo

The first step is to create an account on Zenodo and generate an API token.
Follow these steps (taken from 
[here](http://developers.zenodo.org/#creating-a-personal-access-token)):

 1. [Register](https://zenodo.org/signup) for a Zenodo account if you 
    don’t already have one.
 2. Go to your 
    [Applications](https://zenodo.org/account/settings/applications/),
    to create a [new 
    token](https://zenodo.org/account/settings/applications/tokens/new/).
 3. Select the OAuth scopes you need (you need at least 
    `deposit:write` and `deposit:actions`).

Now add a set of minimal metadata (required by Zenodo, otherwise 
uploading will fail).

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

Enter the token obtained when prompted. Alternatively, this command 
checks the environment for a `POPPER_ZENODO_API_TOKEN` variable and, 
if available, uses it to authenticate with the service.

By default, the `archive` command will only upload the snapshot of the 
project but will not publish it. In order to publish and generate a 
DOI for the archive, pass the `--publish` flag to the `archive` 
command:

```bash
popper archive --service zenodo --publish
```

A URL containing the DOI will be printed to the terminal.

### FigShare

Create a personal token using the following steps:

1. Go to <https://figshare.com> and create a new account.
2. Go to the [Applications](https://figshare.com/account/applications) 
   section of your profile and in the bottom click on `Create Personal 
   Token`.
3. Keep the token safe for use in the next step.

Now add the list of minimal metadata entries (required by FigShare, 
otherwise uploading will fail).

```bash
popper metadata --add title='Popper test archive'
popper metadata --add author1='Test Author, testauthor@gmail.com, popper'
popper metadata --add abstract='A short description of the article'
popper metadata --add keywords='comma, separated, keywords'
popper metadata --add categories='1656'
```

After this, the `popper archive` command is used to perform the 
archiving.

```bash
popper archive --service figshare
```

Enter the token obtained when prompted. Alternatively, this command 
checks the environment for a `POPPER_FIGSHARE_API_TOKEN` variable and, 
if available, uses it to authenticate with the service.

By default, the `archive` command will only upload the snapshot of the 
project but will not publish it. In order to publish and generate a 
DOI for the archive, pass the `--publish` flag to the `archive` 
command:

```bash
popper archive --service figshare --publish
```

A URL containing the DOI will be printed to the terminal.

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

That is, it contains three pipelines named `paper`,`data-generation` 
and `analysis`. The `.popper.yml` for this project looks like:

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

At the top-level of the YAML file there are entries named `pipelines`, 
`metadata` and `popperized`.

### Pipelines

The `pipelines` YAML entry specifies the details for all the available 
pipelines. For each pipeline, there is information about:

   *  the environment(s) in which the pipeline is be executed.
   *  the path to that pipeline.
   *  the various stages that are present in it.

The special `paper` pipeline is generated by executing `popper init 
paper` and has by default a single stage named `build.sh`.

#### `envs`

The `envs` entry in `.popper.yml` specifies the environment in which a 
pipeline is executed as part of the `popper run` command. By default, 
a pipeline runs on the host, i.e. the same environment where the 
`popper` command runs. By leveraging Docker, a pipeline can run on an 
environment different to the host. The list of available environments 
can be shown by running:

```
popper env --ls
```

By default, the `host` is the registered environment when running 
`popper init`. The `--env` flag of the `init` subcommand can be used 
to specify another environment. For example:

```bash
popper init mypipe --env=alpine-3.4
```

The above specifies that the pipeline named `mypipe` will be executed 
inside a docker container using the `falsifiable/popper:alpine-3.4` 
image.

To add more environment(s):

```bash
popper env mypipe --add ubuntu-xenial,centos-7.2
```

To deregister an environment:

```bash
popper env mypipe --rm centos-7.2
```

Arbitrary images can be specified. The only requirement from the point 
of view of Popper is that they must have `popper` installed in the 
image. For example:

```bash
popper env mypipe --add my-docker-repo/image-with-popper-inside
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
  --stages 'preparation,execution,validation'
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
popper metadata `--add KEY=VALUE` command.
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

### Popperized Repositories and Organizations

The `popperized` YAML entry specifies the list of Github organizations 
and repositories that contain popperized pipelines. By default, it 
points to the `github/popperized` organization. This list is used to 
look for pipelines as part of the `popper search` command.
