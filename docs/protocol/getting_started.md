# Getting Started

_Popper_ is a convention for organizing an academic article's 
artifacts following a [DevOps](https://en.wikipedia.org/wiki/DevOps) 
approach, with the goal of making it easy for others (and yourself!) 
to repeat an experiment.

## Quickstart Guide

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

> **NOTE**: this exercise was written using 0.4.1.

Create a project repository (if you are not familiar with git, look [here](https://www.learnenough.com/git-tutorial)):

```bash
mkdir mypaper
cd mypaper
git init
echo '# mypaper' > README.md
git add .
git commit -m 'first commit'
```

Initialize the popper repository and add the commit file to git:

```bash
popper init
git add .
git commit -m 'adds .popper.yml file'
```

### New experiment

Initialize experiment using `init` (scaffolding):

```bash
popper init myexp
```

Show what this did:

```bash
ls -l experiments/myexp
```

Commit the "empty" experiment:

```bash
git add experiments/myexp
git commit -m 'adding myexp scaffold'
```

### Add existing experiment

List available experiment templates:

```bash
popper search
```

Show information about an experiment:

```bash
popper info blis
```

Import an available experiment:

```bash
popper add blis
```

Commit the new experiment:

```bash
git add experiments/blis
git commit -m 'adding blis baseline'
```

### Popper check

Run popper check:

```bash
popper check
```

Show logs for blis experiment:

```bash
ls -l experiments/blis/popper_logs
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
