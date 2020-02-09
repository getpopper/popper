# Getting Started

Popper is a workflow execution engine based on [Github Actions][gha]
(GHA) written in Python. With Popper, you can execute [HCL
syntax][ghalang] workflows locally on your machine without having
to use Github's platform.

## Installation

We provide a [`pip`][pip] package for Popper. To install simply run:

```bash
pip install popper
```

Depending on your Python distribution or specific environment
configuration, using [Pip][pip] might not be possible (e.g. you need
administrator privileges) or using `pip` directly might incorrectly
install Popper. We **highly recommend** to install Popper in a Python
virtual environment using [virtualenv][venv]. The following
installation instructions assume that `virtualenv` is installed in
your environment (see [here for more][venv-install]). Once
`virtualenv` is available in your machine, we proceed to create a
folder where we will place the Popper virtual environment:

```bash
# create a folder for storing virtual environments
mkdir $HOME/virtualenvs
```

We then create a `virtualenv` for Popper. This will depend on the
method with which `virtualenv` was installed. Here we present three
alternatives that cover most of these alternatives:

```bash
# 1) virtualenv installed via package, e.g.:
# - apt install virtualenv (debian/ubuntu)
# - yum install virtualenv (centos/redhat)
# - conda install virtualenv (conda)
# - pip install virtualenv (pip)
virtualenv $HOME/virtualenvs/popper

# 2) virtualenv installed via Python 3.6+ built-in module
python -m venv $HOME/virtualenvs/popper
```

> **NOTE**: in the case of `conda`, we recommend the creation of a new
> environment before `virtualenv` is installed in order to avoid
> issues with packages that might have been installed previously.

We then load the environment we just created above:

```bash
source $HOME/virtualenvs/popper/bin/activate
```

Finally, we install Popper in this environment using `pip`:

```bash
pip install popper
```

To test all is working as it should, we can show the version we
installed:

```bash
popper version
```

And to get a list of available commands:

```bash
popper --help
```

> **NOTE**: given that we are using `virtualenv`, once the shell
session is ended (when we close the terminal window or tab), the
environment is unloaded and newer sessions (new window or tab) will
not have the `popper` command available in the `PATH` variable. In
order to have the environment loaded again we need to execute the
`source` command (see above). In the case of `conda` we need to load
the Conda environment (`conda activate` command).

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
needs, please take a look at the [workflow language
documentation](gha_workflows.md) read [this tutorial][ghatut], or take
a look at [some examples][ex].

## Run your workflow

To execute the workflow you just created:

```bash
popper run
```

You should see the output of actions printed to the terminal.

To better understand what the above code does, we include a help flag:

```bash
popper run --help
```

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

## More Information

Popper commands allow you to pass `--help` flag to it to get more information about what the command does.

Examples of commands you can get more information about are included (but not limited to) here:

```bash
popper --help
popper ci --help
popper run --help
```

Go to the TravisCI website to see your experiments being executed.

[ghalang]: https://github.com/actions/workflow-parser/blob/master/language.md
[pip]: https://pip.pypa.io/en/stable/
[wfdocs]: gha_workflows.md
[ghatut]: https://scotch.io/bar-talk/introducing-github-actions#toc-how-it-works
[ex]: https://github.com/popperized/popper-examples
[gh-create]: https://help.github.com/articles/create-a-repo/
[cisetup]: https://docs.travis-ci.com/user/getting-started/#Prerequisites
[ciactivate]: https://docs.travis-ci.com/user/getting-started/#To-get-started-with-Travis-CI
[gha]: https://github.com/features/actions
[venv]: https://virtualenv.pypa.io/en/latest/
[venv-install]: https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/#installing-virtualenv
