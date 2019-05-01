# Getting Started

Popper is a workflow execution engine based on [Github 
Actions](https://github.com/features/actions) written in Python. With 
Popper, you can execute workflows locally on your machine without 
having to use Github's platform. To get started, we first need to 
install the CLI tool using [Pip](https://pip.pypa.io/en/stable/):

```bash
pip install popper
```

Show which version you installed:

```bash
popper version
```

> **NOTE**: Any version greater than 2.0 is currently officially 
> supported.

To get a list of available commands:

```bash
popper --help
```

## Create a Git repository

Create a project repository (if you are not familiar with Git, look 
[here](https://www.learnenough.com/git-tutorial)):

```bash
mkdir mypaper
cd mypaper
git init
echo '# mypaper' > README.md
git add .
git commit -m 'first commit'
```

## Link to GitHub repository

First, create a repository [on 
Github](https://help.github.com/articles/create-a-repo/). Once your 
Github repository has been created, register it as a remote repository 
on your local repository:

```bash
git remote add origin git@github.com:<user>/<repo>
```

where `<user>` is your username and `<repo>` is the name of the 
repository you have created. Then, push your local commits:

```bash
git push -u origin master
```

## Create a workflow

We need to create a `.workflow` file:

```bash
popper scaffold
```

The above generates an example workflow that you can use as the 
starting point of your project. We first commit the files that got 
generated:

```bash
git add .
git commit -m 'Adding example workflow.'
git push
```

To learn more about how to modify this workflow in order to fit your 
needs, please take a look at the [official 
documentation](https://developer.github.com/actions/managing-workflows/creating-and-cancelling-a-workflow/), 
read [this 
tutorial](https://scotch.io/bar-talk/introducing-github-actions#toc-how-it-works) 
or take a look at [some examples](examples.html).

## Run your workflow

To execute the workflow you just created:

```bash
popper run
```

You should see the output of actions printed to the terminal.

## Continuously Run Your Workflow on Travis

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

Go to the TravisCI website to see your experiments being executed.
