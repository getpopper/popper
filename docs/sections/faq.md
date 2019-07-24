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

The `popper run` takes an optional `action` argument that can be used 
to execute a workflow up to a certain step. See 
[here](cli_features.html).

### Installing Popper shows a `pyhcl` error

This project uses `pyhcl`, and when `pip` installs Popper, in some 
cases the below error is reported but it can be safely ignored.

```bash
Building wheels for collected packages: pyhcl
  Building wheel for pyhcl (setup.py) ... error
  ERROR: Complete output from command /Users/ivo/virtualenvs/test/bin/python3.7 -u -c 'import setuptools, tokenize;__file__='"'"'/private/var/folders/6c/pl43v
kgd0f5c29ffsnvkwvth0000gn/T/pip-install-kv3rwdd9/pyhcl/setup.py'"'"';f=getattr(tokenize, '"'"'open'"'"', open)(__file__);code=f.read().replace('"'"'\r\n'"'"',
 '"'"'\n'"'"');f.close();exec(compile(code, __file__, '"'"'exec'"'"'))' bdist_wheel -d /private/var/folders/6c/pl43vkgd0f5c29ffsnvkwvth0000gn/T/pip-wheel-8m6v
ve9q --python-tag cp37:
  ERROR: running bdist_wheel
  running build
  running build_py
  Generating parse table...
  Traceback (most recent call last):
    File "<string>", line 1, in <module>
    File "/private/var/folders/6c/pl43vkgd0f5c29ffsnvkwvth0000gn/T/pip-install-kv3rwdd9/pyhcl/setup.py", line 101, in <module>
      "Topic :: Text Processing",
    File "/usr/local/Cellar/python/3.7.2_2/Frameworks/Python.framework/Versions/3.7/lib/python3.7/distutils/core.py", line 148, in setup
      dist.run_commands()
    File "/usr/local/Cellar/python/3.7.2_2/Frameworks/Python.framework/Versions/3.7/lib/python3.7/distutils/dist.py", line 966, in run_commands
      self.run_command(cmd)
    File "/usr/local/Cellar/python/3.7.2_2/Frameworks/Python.framework/Versions/3.7/lib/python3.7/distutils/dist.py", line 985, in run_command
      cmd_obj.run()
    File "/Users/ivo/virtualenvs/test/lib/python3.7/site-packages/wheel/bdist_wheel.py", line 192, in run
      self.run_command('build')
    File "/usr/local/Cellar/python/3.7.2_2/Frameworks/Python.framework/Versions/3.7/lib/python3.7/distutils/cmd.py", line 313, in run_command
      self.distribution.run_command(command)
    File "/usr/local/Cellar/python/3.7.2_2/Frameworks/Python.framework/Versions/3.7/lib/python3.7/distutils/dist.py", line 985, in run_command
      cmd_obj.run()
    File "/usr/local/Cellar/python/3.7.2_2/Frameworks/Python.framework/Versions/3.7/lib/python3.7/distutils/command/build.py", line 135, in run
      self.run_command(cmd_name)
    File "/usr/local/Cellar/python/3.7.2_2/Frameworks/Python.framework/Versions/3.7/lib/python3.7/distutils/cmd.py", line 313, in run_command
      self.distribution.run_command(command)
    File "/usr/local/Cellar/python/3.7.2_2/Frameworks/Python.framework/Versions/3.7/lib/python3.7/distutils/dist.py", line 985, in run_command
      cmd_obj.run()
    File "/private/var/folders/6c/pl43vkgd0f5c29ffsnvkwvth0000gn/T/pip-install-kv3rwdd9/pyhcl/setup.py", line 39, in run
      self.execute(_pre_install, (), msg="Generating parse table...")
    File "/usr/local/Cellar/python/3.7.2_2/Frameworks/Python.framework/Versions/3.7/lib/python3.7/distutils/cmd.py", line 335, in execute
      util.execute(func, args, msg, dry_run=self.dry_run)
    File "/usr/local/Cellar/python/3.7.2_2/Frameworks/Python.framework/Versions/3.7/lib/python3.7/distutils/util.py", line 286, in execute
      func(*args)
    File "/private/var/folders/6c/pl43vkgd0f5c29ffsnvkwvth0000gn/T/pip-install-kv3rwdd9/pyhcl/setup.py", line 31, in _pre_install
      import hcl
    File "/private/var/folders/6c/pl43vkgd0f5c29ffsnvkwvth0000gn/T/pip-install-kv3rwdd9/pyhcl/src/hcl/__init__.py", line 1, in <module>
      from .api import dumps, load, loads
    File "/private/var/folders/6c/pl43vkgd0f5c29ffsnvkwvth0000gn/T/pip-install-kv3rwdd9/pyhcl/src/hcl/api.py", line 2, in <module>
      from .parser import HclParser
    File "/private/var/folders/6c/pl43vkgd0f5c29ffsnvkwvth0000gn/T/pip-install-kv3rwdd9/pyhcl/src/hcl/parser.py", line 4, in <module>
      from .lexer import Lexer
    File "/private/var/folders/6c/pl43vkgd0f5c29ffsnvkwvth0000gn/T/pip-install-kv3rwdd9/pyhcl/src/hcl/lexer.py", line 3, in <module>
      import ply.lex as lex
  ModuleNotFoundError: No module named 'ply'
  ----------------------------------------
  ERROR: Failed building wheel for pyhcl
  Running setup.py clean for pyhcl
Failed to build pyhcl
```
