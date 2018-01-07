# Getting Started

_Popper_ is a convention for organizing an academic article's 
artifacts following a [DevOps](https://en.wikipedia.org/wiki/DevOps) 
approach, with the goal of making it easy for others (and yourself!) 
to repeat an experiment or analysis pipeline.

We first need to install the CLI tool by following [these 
instructions](https://github.com/systemslab/popper/tree/master/popper#install). 
Show the available commands:

```bash
popper help
```

Show which version you installed:

```bash
popper version
```

> **NOTE**: this exercise was written using 0.5

Create a project repository (if you are not familiar with git, look [here](https://www.learnenough.com/git-tutorial)):

```bash
mkdir mypaper
cd mypaper
git init
echo '# mypaper' > README.md
git add .
git commit -m 'first commit'
```

Initialize the popper repository and add the `.popper.yml` file to 
git:

```bash
popper init
git add .
git commit -m 'adds .popper.yml file'
```

### New pipeline

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

### Popper check

Run popper check:

```bash
popper check
```

> **NOTE:** By default, `popper check` runs all commands directly on 
the host. We recommend running an isolated environment. In order to do 
this, one can create a pipeline using the `--env` flag of the `popper 
init` command. For example, `popper init <pipeline> --env=alpine-3.4` 
runs a command inside an `alpine-3.4` container.

Once a pipeline is checked, one can show the logs:

```bash
ls -l pipelines/myexp/popper_logs
```

### Adding Project to GitHub

Create a repository on github and upload our commits.

### Adding Project to Travis

For this, we need an account at Travis CI. Once we have one, we 
activate the project so it is continuously validated.

Generate `.travis.yml` file:

```bash
popper ci travis
```

And commit the file:

```bash
git add .travis.yml
git commit -m 'Adds TravisCI config file'
```

Trigger an execution by pushing to github:

```bash
git push
```

Go to TravisCI website to see your experiments being executed.


## Learn More

A more detailed description of Popper is explained in [the next 
section](intro_to_popper.html).

A [step-by-step guide](../tutorial/from_scratch.html) describes how to 
"Popperize" a repository. Additionally, the following is a list of 
examples on how to bootstrap a Popper project (repository) in specific 
domains:

  * [Data Science](../tutorial/data-science.html)
  * [High Performance Computing (HPC)](../tutorial/hpc.html)
  * [Mathematical Sciences](../tutorial/math_science.html)

A list of articles describing the Popper protocol, as well as other 
Popperized papers that have been submitted for publication can be 
found [here](https://falsifiable.us/pubs).
