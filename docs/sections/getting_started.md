# Getting Started

_Popper_ is a convention for organizing an academic article's 
artifacts following a [DevOps](https://en.wikipedia.org/wiki/DevOps) 
approach, with the goal of making it easy for others (and yourself!) 
to repeat an experiment or analysis pipeline.

We first need to install the CLI tool by following [these 
instructions](https://github.com/systemslab/popper/tree/master/cli#install). 
Show the available commands:

```bash
popper --help
```

Show which version you installed:

```bash
popper version
```

> **NOTE**: this exercise was written using 1.0.0

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

## New pipeline

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

## Popper Run

Run popper run:

```bash
popper run
```

Once a pipeline is executed, one can show the logs:

```bash
ls -l pipelines/myexp/popper_logs
```

## Adding Project to GitHub

Create a repository [on 
github](https://help.github.com/articles/create-a-repo/), register the 
remote repository to your local git and push all your commits:

```bash
git remote add origin git@github.com:<user>/<repo>
git push -u origin master
```

where `<user>` is your username and `<repo>` is the name of the 
repository you have created.

## Adding Project to Travis

For this, we need to [login to Travis 
CI](https://docs.travis-ci.com/user/getting-started/#Prerequisites) 
using our Github credentials. Once this is done, we [activate the 
project](https://docs.travis-ci.com/user/getting-started/#To-get-started-with-Travis-CI) 
so it is continuously validated.

Generate `.travis.yml` file:

```bash
popper ci --service travis
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

