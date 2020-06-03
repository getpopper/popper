# FAQ

### How can I create a virtual environment to install Popper

The following creates a virtual environment in a `$HOME/venvs/popper` 
folder:

```bash
# create virtualenv
virtualenv $HOME/venvs/popper

# activate it
source $HOME/venvs/popper/bin/activate

# install Popper in it
pip install popper
```

The first step is is only done once. After closing your shell, or 
opening another tab of your terminal emulator, you'll have to reload 
the environment (`activate it` line above). For more on virtual 
environments, see 
[here](https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/#installing-virtualenv).

### How can we deal with large datasets? For example I have to work on large data of hundreds GB, how would this be integrated into Popper?

For datasets that are large enough that they cannot be managed by Git, 
solutions such as a PFS, GitLFS, Datapackages, ckan, among others 
exist. These tools and services allow users to manage large datasets 
and version-control them. From the point of view of Popper, this is 
just another tool that will get invoked as part of the execution of a 
pipeline. As part of our documentation, we have examples on how to use 
datapackages, and another on how to use data.world.

### How can Popper capture more complex workflows? For example, automatically restarting failed tasks?

A Popper pipeline is a simple sequence of "containerized bash 
scripts". Popper is not a replacement for scientific workflow engines, 
instead, its goal is to capture the highest-most workflow: the human 
interaction with a terminal.

### Can I follow Popper in computational science research, as opposed to computer science?

Yes, the goal for Popper is to make it a domain-agnostic 
experimentation protocol. See the 
<https://github.com/popperized/popper-examples> repository for 
examples.

### How to apply the Popper protocol for applications that take large quantities of computer time?

The `popper run` takes an optional `STEP` argument that can be used to 
execute a workflow up to a certain step. Run `popper run --help` for 
more.
