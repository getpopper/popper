# Guides

This is a list of guides related to several aspects of working with 
Github Action (GHA) workflows.

## Creating a new action

You can create actions in a repository you own by adding a 
`Dockerfile`. To share GitHub Actions with the GitHub community, your 
repository must be public. All actions require a `Dockerfile`. An 
action may also include an `entrypoint.sh` file, to execute arguments, 
and any other files that contain the action\'s code. For example, an 
action called `action-a` might have this directory structure:

```
|-- hello-world (repository)
|   |__ main.workflow
|   |__ action-a
|       │__  Dockerfile
|       │__  README.md
|       |__  entrypoint.sh
|
```

To use an action in your repository, refer to the action in your 
`.workflow` using a path relative to the repository directory. For 
example, if your repository had the directory structure above, you 
would use this relative path to use `action-a` in a workflow for the 
`hello-world` repository:

```hcl
action "action a" {
  uses = "./action-a/"
}
```

Every action should have a `README.md` file in the action\'s 
subdirectory that includes this information:

  - A detailed description of what the action does.
  - [Environment variables][env-vars] the action uses.
  - [Secrets][secrets] the action uses. Production secrets should not 
    be stored in the API during the limited public beta period.
  - Required arguments.
  - Optional arguments.

See [Creating a Docker container]() to learn more about creating a 
custom Docker container and how you can use `entrypoint.sh`.

### Choosing a location for your action

If you are developing an action for other people to use, GitHub
recommends keeping the action in its own repository instead of bundling
it with other application code. This allows you to version, track, and
release the action just like any other software. Storing an action in
its own repository makes it easier for the GitHub community to discover
the action, narrows the scope of the code base for developers fixing
issues and extending the action, and decouples the action\'s versioning
from the versioning of other application code.

### Using shell scripts to create actions

Shell scripts are a great way to write the code in GitHub Actions. If
you can write an action in under 100 lines of code and it doesn\'t
require complex or multi-line command arguments, a shell script is a
great tool for the job. When writing actions using a shell script,
following these guidelines:

-   Use a POSIX-standard shell when possible. Use the `#!/bin/sh`
    [shebang](https://en.wikipedia.org/wiki/Shebang_(Unix)) to use the
    system\'s default shell. By default, Ubuntu and Debian use the
    [dash](https://wiki.ubuntu.com/DashAsBinSh) shell, and Alpine uses
    the [ash](https://en.wikipedia.org/wiki/Almquist_shell) shell. Using
    the default shell requires you to avoid using bash or shell-specific
    features in your script.
-   Use `set -eu` in your shell script to avoid continuing when errors
    or undefined variables are present.

### Hello world action example

You can create a new action by adding a `Dockerfile` to the directory 
in your repository that contains your action code. This example 
creates a simple action that writes arguments to standard output 
(`stdout`). An action declared in a `main.workflow` would pass the 
arguments that this action writes to `stdout`. To learn more about the 
instructions used in the `Dockerfile`, check out the [official Docker 
documentation][howto-dockerfile]. The two files you need to create an 
action are shown below:

**./action-a/Dockerfile**

```Dockerfile
FROM debian:9.5-slim

ADD entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
```

**./action-a/entrypoint.sh**

```bash
#!/bin/sh -l

sh -c "echo $*"
```

Your code must be executable. Make sure the `entrypoint.sh` file has
`execute` permissions before using it in a workflow. You can modify the
permission from your terminal using this command:

```bash
chmod +x entrypoint.sh
```

This action `echo`s the arguments you pass the action. For example, if
you were to pass the arguments `"Hello World"`, you\'d see this output
in the command shell:

```bash
Hello World
```

## Creating a Docker container

Check out the [official Docker documentation][howto-dockerfile].

[howto-dockerfile]: https://docs.docker.com/engine/reference/builder/

## Implementing a workflow for an existing set of scripts

This guide exemplifies how to define a Github Action (GHA) workflow 
for an existing set of scripts. Assume we have a project in a 
`myproject/` folder and a list of scripts within the 
`myproject/scripts/` folder, as shown below:

```bash
cd myproject/
ls -l scripts/

total 16
-rwxrwx---  1 user  staff   927B Jul 22 19:01 download-data.sh
-rwxrwx---  1 user  staff   827B Jul 22 19:01 get_mean_by_group.py
-rwxrwx---  1 user  staff   415B Jul 22 19:01 validate_output.py
```

A straight-forward workflow for wrapping the above is the following:

```hcl
workflow "co2 emissions" {
  resolves = "validate results"
}

action "download data" {
  uses = "popperized/bin/sh@master"
  args = ["scripts/download-data.sh"]
}

action "run analysis" {
  needs = "download data"
  uses = "popperized/bin/sh@master"
  args = ["workflows/minimal-python/scripts/get_mean_by_group.py", "5"]
}

action "validate results" {
  needs = "run analysis"
  uses = "popperized/bin/sh@master"
  args = [
    "workflows/minimal-python/scripts/validate_output.py",
    "workflows/minimal-python/data/global_per_capita_mean.csv"
  ]
}
```

The above runs every script within a Docker container, whose image is 
the one associated to the `popperized/bin/sh` action (see corresponding 
Github repository [here][shaction]). As you would expect, this 
workflow fails to run since the `popperized/bin/sh` image is a 
lightweight one (contains only Bash utilities), and the dependencies 
that the scripts need are not be available in this image. In cases 
like this, we need to either [use an existing action][search] that has 
all the dependencies we need, or [create an action ourselves][create].

In this particular example, these scripts depend on CURL and Python. 
Thankfully, actions for these already exist, so we can make use of 
them as follows:

```hcl
workflow "co2 emissions" {
  resolves = "validate results"
}

action "download data" {
  uses = "popperized/bin/curl@master"
  args = [
    "--create-dirs",
    "-Lo workflows/minimal-python/data/global.csv",
    "https://github.com/datasets/co2-fossil-global/raw/master/global.csv"
  ]
}

action "run analysis" {
  needs = "download data"
  uses = "jefftriplett/python-actions@master"
  args = [
    "workflows/minimal-python/scripts/get_mean_by_group.py",
    "workflows/minimal-python/data/global.csv",
    "5"
  ]
}

action "validate results" {
  needs = "run analysis"
  uses = "jefftriplett/python-actions@master"
  args = [
    "workflows/minimal-python/scripts/validate_output.py",
    "workflows/minimal-python/data/global_per_capita_mean.csv"
  ]
}
```

The above workflow runs correctly anywhere where Github Actions 
workflow can run.

> _**NOTE**: The `download-data.sh` contained just one line invoking 
> CURL, so we make that call directly in the action block and remove 
> the bash script._

### When no container runtime is available

In scenarios where a container runtime is not available, the special 
`sh` value for the `uses` attribute of action blocks can be used. This 
value instructs Popper to execute actions directly on the host machine 
(as opposed to executing in a container runtime). The example workflow 
above would be rewritten as:

```hcl
workflow "co2 emissions" {
  resolves = "validate results"
}

action "download data" {
  uses = "sh"
  args = [
    "curl", "--create-dirs",
    "-Lo workflows/minimal-python/data/global.csv",
    "https://github.com/datasets/co2-fossil-global/raw/master/global.csv"
  ]
}

action "run analysis" {
  needs = "download data"
  uses = "sh"
  args = [
    "workflows/minimal-python/scripts/get_mean_by_group.py",
    "workflows/minimal-python/data/global.csv",
    "5"
  ]
}

action "validate results" {
  needs = "run analysis"
  uses = "sh"
  args = [
    "workflows/minimal-python/scripts/validate_output.py",
    "workflows/minimal-python/data/global_per_capita_mean.csv"
  ]
}
```

The obvious downside of running actions directly on the host is that 
dependencies assumed by the scripts might not be available in other 
environments where the workflow is being re-executed. Since there are 
no container images associated to actions that use `sh`, this will 
likely break the portability of the workflow. In this particular 
example, if the workflow above runs on a machine without CURL or on 
Python 2.7, it will fail.

> _**NOTE**: The `uses = "sh"` special value is not supported by the 
> Github Actions platform. This workflow will fail to run on GitHub's 
> infrastructure and can only be executed using Popper._

[shaction]: https://github.com/popperized/bin/tree/master/sh
[search]: https://medium.com/getpopper/searching-for-existing-github-actions-has-never-been-easier-268c463f0257
[create]: https://developer.github.com/actions/creating-github-actions/
