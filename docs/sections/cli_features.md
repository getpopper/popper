# CLI feautures

## New workflow initialization

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

Initialize a workflow

```bash
popper scaffold
```

Show what this did:

```bash
ls -l
```

Commit the "empty" pipeline:

```bash
git add .
git commit -m 'adding my first workflow'
```

## Executing a workflow

To run the workflow:

```bash
popper run
```

or to execute all the workflows in a project:

```bash
popper run --recursive
```

## Environment Variables

Popper defines the same environment variables that are [defined by the 
official Github Actions 
runner](https://developer.github.com/actions/creating-github-actions/accessing-the-runtime-environment/#environment-variables). 
To see the values assigned to these variables, run the following 
workflow:

```hcl
workflow "env workflow" {
  resolves = "show env"
}

action "show env" {
  uses = "actions/bin/sh@master"
  args = ["env"]
}
```

## Reusing existing workflows

Many times, when starting an experiment, it is useful to be able to use
an existing workflow as a scaffold for the one we wish to write. The 
[`popper-examples` 
repository](https://github.com/popperized/popper-examples) contains a 
list of example workflows and actions for the purpose of both learning 
and to use them as a starting point. Another examples can be found on 
Github's [official `actions` 
organization](https://github.com/actions).

Once you have found a workflow you're interested in importing, you can 
use the `popper add` command to obtain a workflow. For example:

```bash
cd myproject/
mkdir myworkflow
popper add https://github.com/popperized/popper-examples/workflows/cloudlab-iperf-test
Downloading workflow data-science as data-science...
Workflow docker-data-science has been added successfully.
```

This will download the contents of the workflow and all its 
dependencies to your project tree.


## Searching for actions

The popper CLI is capable of searching for premade actions that
you can use in your workflows.

You can use the `popper search` command to search for actions
based on a search keyword. For example, to search for npm based actions,
you can simply run:

```bash
$ popper search npm
Matched actions :

> actions/npm
```

Additionally, when searching for an action, you may choose to include
the contents of the readme in your search by using the `--include-readme`
flag.

Once `popper search` runs, it caches all the metadata related to the search.
So, to get the latest releases of the actions, you might want to update the
cache using the `--update-cache` flag.

By default, popper searches for actions from a list present [here](../../cli/popper/resources/.search_sources.yml).
To help the list keep growing, you can add Github organization names or repository
names(org/repo) and send a pull request to the upstream repository.


To get the details of a searched action, use the `popper info` command. For example,

```bash
popper info popperized/cmake
An action for building CMake projects.
```


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

## Visualizing workflows

While `.workflow` files are relatively simple to read, it is nice to 
have a way of quickly visualizing the steps contained in a workflow. 
Popper provides the option of generating a graph for a workflow. To 
generate a graph for this pipeline, execute the following:

```bash
popper dot
```

The above generates a graph in `.dot` format. To visualize it, you can 
install the [`graphviz`](https://graphviz.gitlab.io/) package and 
execute:

```bash
popper dot | dot -T png -o wf.png
```

The above generates a `wf.png` file depicting the workflow. 
Alternatively you can use the <http://www.webgraphviz.com/> website to 
generate a graph by copy-pasting the output of the `popper dot` 
command.
