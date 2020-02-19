# Getting Started

Popper is a [container-native][cn] [workflow execution engine][wfeng]. 
A container-native workflow is one where all steps contained in it are 
executed in containers. Before going through this guide, you need to 
have the Docker engine installed on your machine (see [installations 
instructions here][docker-install]), as well as a Python installation 
capable of adding packages via [Pip][pip] or [Virtualenv][venv].

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
method with which `virtualenv` was installed:

```bash
# 1) if virtualenv was installed via package, e.g.:
# - apt install virtualenv (debian/ubuntu)
# - yum install virtualenv (centos/redhat)
# - conda install virtualenv (conda)
# - pip install virtualenv (pip)
virtualenv $HOME/virtualenvs/popper

# OR
#
# 2) if virtualenv installed via Python 3.6+ module
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
session ends (when we close the terminal window or tab), the 
environment gets unloaded and newer sessions (new window or tab) will 
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

> **NOTE**: if you run on MacOS, make sure the `myproject/` folder is 
> in a folder that is shared with the Docker engine. By default, 
> Docker For Mac shares the `/Users` folder, so putting the 
> `myproject/` folder in any subfolder of `/Users/<USERNAME>/` should 
> suffice. Otherwise, if you want to put it on an folder other than 
> `/Users`, you will need to modify the Docker For Mac settings so 
> that this other folder is also shared with the underlying Linux VM.

## Create a workflow

We create a small, pre-defined workflow by running:

```bash
popper scaffold
```

The above generates an example workflow that you can use as the 
starting point of your project. This minimal example illustrates two 
distinct ways in which a `Dockerfile` image can be used in a workflow 
(by pulling an image from a registry, or by referencing one stored in 
a public repository). To show the content of the workflow:

```bash
cat wf.yml
```

For each step in the workflow, an image is created (or pulled) and a 
container is instantiated. For a more detailed description of how 
Popper processes a workflow, take a look at the ["Workflow Language 
and Runtime"](cn_workflows.md) section. To learn more on how to modify 
this workflow in order to fit your needs, take a look at [this 
tutorial][ghatut] or take a look at [some examples][ex].

Before we go ahead and test this workflow, we first commit the files 
to the Git repository:

```bash
git add .
git commit -m 'Adding example workflow.'
```

## Run your workflow

To execute the workflow you just created:

```bash
popper run -f wf.yml
```

You should see the output printed to the terminal that informs of the 
three main tasks that Popper executes for each step in a workflow: 
build (or pull) a container image, instantiate a container, and 
execute the step by invoking the specified command within the 
container.

> **TIP:** Type `popper run --help` to learn more about other options 
> available and a high-level description of what this command does.

Since this workflow consists of two steps, there were two 
corresponding containers that were executed by the underlying 
container engine, which is Docker in this case. We can verify this by 
asking Docker to show the list of existing containers:

```bash
docker ps -a
```

You should see the two containers from the example workflow being 
listed.

To obtain more detailed information of what this command does, you can pass the `--help` flag to it:

```bash
popper run --help
```

> **NOTE**: All Popper subcommands allow you to pass `--help` flag to it to get more information about what the command does.

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

Go to the TravisCI website to see your experiments being executed.

## Next Steps

For a detailed description of how Popper processes workflows, take a 
look at the ["Workflow Language and Runtime"](cn_workflows.md) 
section. To learn more on how to modify workflows to fit your needs, 
take a look at [this tutorial][ghatut] or at [some examples][ex].

[docker-install]: https://docs.docker.com/install/
[wfeng]: https://en.wikipedia.org/wiki/Workflow_engine
[cn]: https://cloudblogs.microsoft.com/opensource/2018/04/23/5-reasons-you-should-be-doing-container-native-development/
[pip]: https://pip.pypa.io/en/stable/
[wfdocs]: gha_workflows.md
[ghatut]: https://popperized.github.io/swc-lesson/
[ex]: https://github.com/popperized/popper-examples
[gh-create]: https://help.github.com/articles/create-a-repo/
[cisetup]: https://docs.travis-ci.com/user/getting-started/#Prerequisites
[ciactivate]: https://docs.travis-ci.com/user/getting-started/#To-get-started-with-Travis-CI
[venv]: https://virtualenv.pypa.io/en/latest/
[venv-install]: https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/#installing-virtualenv
