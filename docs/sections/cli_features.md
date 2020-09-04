# CLI features

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

Show what this did (a `wf.yml` should have been created):

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
popper run -f wf.yml
```

where `wf.yml` is a file containing a workflow.

## Executing a step interactively

For debugging a workflow, it is sometimes useful to open a shell 
inside a container associated to a step of a workflow. To accomplish 
this, run:

```bash
popper sh <STEP>
```

where `<STEP>` is the name of a step contained in the workflow. For 
example, given the following workflow:

```yaml
steps:
- id: mystep
  uses: docker://ubuntu:18.04
  runs: ["ls", "-l"]
  dir: /tmp/
  env:
    MYENVVAR: "foo"
```

if we want to open a shell that puts us inside the `mystep` above 
(inside an container instance of the `ubuntu:18.04` image), we run:

```bash
popper sh mystep
```

And this opens an interactive shell inside that step, where the 
environment variable `MYENVVAR` is available. Note that the `runs` and 
`args` attributes are overridden by Popper. By default, `/bin/bash` is 
used to start the shell, but this can be modified with the 
`--entrypoint` flag.

## Parametrizing workflows with substitutions

A workflow can be parametrized by making use of substitutions. A 
substitution is a string in the YAML file with the `$_` prefix, for 
example:

```yaml
steps:
- id: mystep
  uses: docker://alpine:$_ALPINE_VERSION
  runs: ["ls", "-l"]
```

in the above workflow, the `$_ALPINE_VERSION` string defines a 
substitution, and will be replaced by a value defined in the command 
line via the `--substutition` or `-s` flags:

```bash
popper run -s _ALPINE_VERSION=3.12 -f wf.yml
```

## Customizing container engine behavior

By default, Popper instantiates containers in the underlying engine by 
using basic configuration options. When these options are not suitable 
to your needs, you can modify or extend them by providing 
engine-specific options. These options allow you to specify 
fine-grained capabilities, bind-mounting additional folders, etc. In 
order to do this, you can provide a configuration file to modify the 
underlying container engine configuration used to spawn containers. 
This is a YAML file that defines an `engine` dictionary with custom 
options and is passed to the `popper run` command via the `--conf` (or 
`-c`) flag.

For example, to make Popper spawn Docker containers in
[privileged mode][privmode], we can write the following option:

```yaml
engine:
    name: docker
    options:
       privileged: True
```

Similarly, to bind-mount additional folders, we can use the `volumes` option to list the directories to mount:

```yaml
engine:
    name: docker
    options:
       privileged: True
       volumes:
       - myvol1:/folder
       - myvol2:/app
```

Assuming the above is stored in a file called `config.yml`, we pass 
it to Popper by running:

```
popper run -f wf.yml -c config.yml
```

> **NOTE**:
>
> Currently, the `--conf` option is only supported for the `docker`engine.

[privmode]: https://docs.docker.com/engine/reference/run/#runtime-privilege-and-linux-capabilities


## Continuously validating a workflow

The `ci` subcommand generates configuration files for multiple CI 
systems. The syntax of this command is the following:

```bash
popper ci --file wf.yml <service-name>
```

Where `<name>` is the name of the CI system (see `popper ci --help` to get a list of 
supported systems). If the `wf.yml` workflow makes use of [substitutions](), we 
can create a matrix by doing:

```bash
popper ci -f wf.yml travis -s _P1=p1v1 -s _P1=p1v2 -s _P2=p2v1 -s _P2=p2v2
```

And the above will create a 2x2 matrix job, doing a parameter sweep over the 
`_P1` and `_P2` given substitution values.


In the following, we show how to link github with some of the supported CI 
systems. In order to do so, we first need to create a repository on github and 
upload our commits:

```bash
# set the new remote
git remote add origin <your-github-repo-url>

# verify the remote URL
git remote -v

# push changes in your local repository up to github
git push -u origin master
```

### TravisCI

In the following, we assume we have an account on [Travis 
CI](http://travis-ci.com). Assuming our repository is already on 
GitHub, we can enable it on TravisCI so that it is continuously 
validated (see 
[here](https://docs.travis-ci.com/user/getting-started/) for a guide). 
Once the project is registered on Travis, we proceed to generate a 
`.travis.yml` file:

```bash
cd my-repo/

popper ci --file wf.yml travis
```

Before we can execute tests on travis, we need to commit the file we 
just generated:

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

#### Job Matrix

If the workflow is parametrized by the use of 
[substitutions](./cli_features.html#parametrizing-workflows-with-substitutions), 
we can create a matrix. For example, assume a workflow like the 
following:

```yaml
steps:
- id: mystep
  uses: docker://alpine:$_ALPINE_VERSION
  runs: [sh, -cue]
  args:
  - |
    # execute command with parameter
    ls -l $_FOLDER
```

```bash
popper ci travis \
  -f wf.yml \
  -s _ALPINE_VERSION=3.10 \
  -s _ALPINE_VERSION=3.11 \
  -s _ALPINE_VERSION=3.12 \
  -s _FOLDER=/root \
  -s _FOLDER=/etc \
  -s _FOLDER=/usr
```

And the above will create a 3x3 matrix job for travis.

## Visualizing workflows

While `.workflow` files are relatively simple to read, it is nice to 
have a way of quickly visualizing the steps contained in a workflow. 
Popper provides the option of generating a graph for a workflow. To 
generate a graph for a pipeline, execute the following:

```bash
popper dot -f wf.yml
```

The above generates a graph in `.dot` format. To visualize it, you can 
install the [`graphviz`](https://graphviz.gitlab.io/) package and 
execute:

```bash
popper dot -f wf.yml | dot -T png -o wf.png
```

The above generates a `wf.png` file depicting the workflow. 
Alternatively you can use the <http://www.webgraphviz.com/> website to 
generate a graph by copy-pasting the output of the `popper dot` 
command.
