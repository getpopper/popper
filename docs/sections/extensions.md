# Extensions

This section describes the extensions Popper brings on top of Github 
Actions.

> **NOTE**: These extensions are **not** supported by the official 
> Github Actions platform. Workflows using these extensions will fail 
> to run on Github's infrastructure and can only be executed using 
> Popper.

## Downloading actions from arbitrary Git repositories

The syntax for defining actions in a workflow is the following:

```hcl
action "IDENTIFIER" {
  needs = "ACTION1"
  uses = "docker://image2"
}
```

The `uses` attribute references Docker images, filesystem paths or 
github repositories (see [syntax documentation][gha-syntax-doc] for 
more). In the case where an action references a public repository, 
Popper extends the syntax in the following way:

```
{url}/{user}/{repo}/{path}@{ref}
```

The `{url}` can reference any Git repository, allowing workflows to 
reference actions outside of Github. For example:

```
action "myaction on gitlab" {
  uses = "git@gitlab.com:user/repo/path/to/my/action@master"
}

action "another one on bitbucket" {
  uses = "https://bitbucket.com/user/repo/action@master"
}
```

The above shows an example of a workflow referencing actions hosted on 
[Gitlab](https://gitlab.com) and [Bitbucket](https://bitbucket.org), 
respectively.

## Other Runtimes

By default, actions in Popper workflows run in Docker, similarly to 
how they run in the Github Actions platform. Popper adds the ability 
of running actions in other runtimes by providing a `--runtime` flag 
to the `popper run` command.

> **NOTE**: As part of our roadmap, we plan to add support for
> [Vagrant](https://www.vagrantup.com/)
> and [Podman](https://podman.io/) runtimes. Open a [new
> issue](https://github.com/systemslab/popper/issues/new) to request 
> another runtime you would want Popper to support.

### Singularity

Popper can execute a workflow in systems where Singularity 3.2+ is 
available. To execute a workflow in Singularity containers:

```bash
popper run --runtime singularity
```

When no `--runtime` option is supplied, Popper executes workflows in 
Docker.

#### Limitations

  * The use of `ARG` in `Dockerfile`s is not supported by Singularity.
  * Currently, the `--reuse` functionality of the `popper run` command 
    is not available when running in Singularity.

### Host

There are situations where a container runtime is not available and 
cannot be installed. In these cases, an action can execute directly on 
the host where the `popper` command is running by making use of the 
special `sh` value for the `uses` attribute. This value instructs 
Popper to execute the command (given in the `args` attribute) or 
script (specified in the `runs` attribute) directly on the host. For 
example:

```hcl
action "run on host" {
  uses = "sh"
  args = ["ls", "-la"]
}

action "another execution on host" {
  uses = "sh"
  runs = "./path/to/my/script.sh"
  args = "args"
}
```

In the first example action above, the `ls -la` command is executed on 
the root of the repository folder (the repository storing the 
`.workflow` file). In the second one shows how to execute a script. 
The obvious downside of running actions on the host is that, depending 
on the command being executed, the workflow might not be portable.

> **NOTE**: The working directory (the value of `$PWD` when a command 
> or script is executed) is the root of the project. Thus, to ensure 
> portability, scripts should make use of paths relative to the root 
> of the folder. If absolute paths are needed, the `$GITHUB_WORKSPACE` 
> variable can be used.

[gha-syntax-doc]: https://developer.github.com/actions/managing-workflows/workflow-configuration-options/#using-a-dockerfile-image-in-an-action
