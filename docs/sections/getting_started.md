# Getting Started

Popper is a workflow execution engine based on [Github Actions][gha] 
written in Python. With Popper, you can execute workflows locally on 
your machine without having to use Github's platform. To get started, 
we first need to install the CLI tool using [Pip][pip]:

```bash
pip install popper
```

Show which version you installed:

```bash
popper version
```

To get a list of available commands:

```bash
popper --help
```

## Create a Git repository

Create a project repository (if you are not familiar with Git, look 
[here](https://www.learnenough.com/git-tutorial)):

```bash
mkdir myproject
cd myproject
git init
echo '# myproject' > README.md
git add .
git commit -m 'first commit'
```

## Create a workflow

First, we create an example `.workflow` file with a pre-defined 
workflow:

```bash
popper scaffold
```

The above generates an example workflow that you can use as the 
starting point of your project. We first commit the files that got 
generated:

```bash
git add .
git commit -m 'Adding example workflow.'
```

To learn more about how to modify this workflow in order to fit your 
needs, please take a look at the [official documentation][ghadocs], 
read [this tutorial][ghatut], or take a look at [some examples][ex].

## Run your workflow

To execute the workflow you just created:

```bash
popper run
```

You should see the output of actions printed to the terminal.

## Link to GitHub repository

Create a repository [on Github][gh-create]. Once your Github 
repository has been created, register it as a remote repository on 
your local repository:

```bash
git remote add origin git@github.com:<user>/<repo>
```

where `<user>` is your username and `<repo>` is the name of the 
repository you have created. Then, push your local commits:

```bash
git push -u origin master
```

## Continuously Run Your Workflow on Travis

For this, we need to [login to Travis CI][cisetup] using our Github 
credentials. Once this is done, we [activate the project][ciactivate] 
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

[pip]: https://pip.pypa.io/en/stable/
[ghadocs]: https://developer.github.com/actions/managing-workflows/creating-and-cancelling-a-workflow/
[ghatut]: https://scotch.io/bar-talk/introducing-github-actions#toc-how-it-works
[ex]: https://github.com/popperized/popper-examples
[gh-create]: https://help.github.com/articles/create-a-repo/
[cisetup]: https://docs.travis-ci.com/user/getting-started/#Prerequisites
[ciactivate]: https://docs.travis-ci.com/user/getting-started/#To-get-started-with-Travis-CI
[gha]: https://github.com/features/actions
