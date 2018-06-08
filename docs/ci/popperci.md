# Popper and CI systems

By following a convention for structuring the files of a project, an 
experimentation pipeline execution and validation can be automated 
without the need for manual intervention. In addition to this, the 
status of a pipeline (integrity over time) can be tracked by a 
[continuous integration (CI) 
service](https://en.wikipedia.org/wiki/Comparison_of_continuous_integration_software). 
In this section we describe how Popper integrates with some existing 
CI services.

## CI System Configuration

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

### TravisCI

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

### CircleCI

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

### Jenkins

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

## CI Functionality

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

## Popper Badges

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

