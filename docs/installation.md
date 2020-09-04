# Installation

We provide an installer, as described in the main 
[README.md](https://github.com/getpopper/popper) of the project. This 
script installs a Popper executable (`popper` binary), and optionally 
places it on `/usr/local/bin/` so that it is available globally on 
your system. The script tells you what is doing and asks for 
confirmation before moving the file to `/usr/local/bin`.

The installer script is the preferred method if Docker is the 
container engine available in your system, as in this case Popper runs 
in Docker itself. For other container engines such as 
[Singularity][sing], you will need to install the Python Package (see 
"Install in a Virtualenv" section). For setting up a development 
environment, see the "Development Setup" section.

[sing]: https://github.com/sylabs/singularity

## Requirements

Popper only runs on Linux or MacOS. On Windows systems, Popper can be 
executed in the [Windows Subsystem for Linux (WSL2)][wsl2]. The only 
requirement for the main installation approach (installer script 
described above), is to have Docker installed. Consult the [official 
Docker documentation][dinstall] for detailed instructions on how to 
install Docker.

Running workflows on Singularity requires Singularity 3.2+ and can 
only be done with Popper installed via via Pip (section below), which 
in turn assumes Python 3.6+.

[wsl2]: https://docs.microsoft.com/en-us/windows/wsl/wsl2-index
[dinstall]: https://docs.docker.com/get-docker/

## Install in a Virtualenv

> If you intent to use Popper for running workflows on Docker, we 
> recommend using the installer script as described at the beginning 
> of this page. Installing via Pip is only necessary if you intend to 
> workflows on Singularity or if you are setting up a development 
> environment.

To install Popper via Pip, we highly recommend doing it in a virtual 
environment using [virtualenv][venv], as opposed to installing 
globally on your system (avoid doing `sudo pip install...` or `pip 
install --user...`), as this usually results in scenarios that are 
difficult to debug.

The following installation instructions assume that `virtualenv` is 
installed in your environment (see [here for more][venv-install]). 
Once `virtualenv` is available in your machine, we proceed to create a 
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

## Development Setup

To create a development environment for hacking on Popper, you can 
execute the following:

```bash
cd $HOME/

# create virtualenv
virtualenv $HOME/venvs/popper
source $HOME/venvs/popper/bin/activate

# clone popper
git clone git@github.com:getpopper/popper
cd popper

# install popper from source
pip install -e src/[dev]
```

the `-e` flag passed to `pip` tells it to install the package from the 
source folder, and if you modify the logic in the popper source code 
you will see the effects when you invoke the `popper` command. So with 
the above approach you have both (1) popper installed in your machine 
and (2) an environment where you can modify popper and test the 
results of such modifications.

[venv]: https://virtualenv.pypa.io/en/latest/
[venv-install]: https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/#installing-virtualenv
