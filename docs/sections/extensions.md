# Extensions

This section describes the extensions Popper brings on top of Github 
Actions.

> **NOTE**: These extensions are NOT supported by the official Github 
> Actions platform.

## Downloading actions from arbitrary Git repositories

The syntax for defining actions in a workflow is the following:

```hcl
action "IDENTIFIER" {
  needs = "ACTION1"
  uses = "docker://image2"
}
```

Other optional [action block 
attributes](https://developer.github.com/actions/managing-workflows/workflow-configuration-options/#using-a-dockerfile-image-in-an-action) 
can be specified. The `uses` attribute references Docker images, 
filesystem paths or github repositories. We reproduce the syntax for 
the `uses` attribute below for convenience:

<table>
<colgroup>
<col style="width: 21%" />
<col style="width: 78%" />
</colgroup>
<thead>
<tr class="header">
<th>Template</th>
<th>Description</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td><span class="title-ref">{user}/{repo}@{ref}</span></td>
<td>A specific branch, ref, or SHA in a public GitHub repository. <strong>Example</strong>: <span class="title-ref">actions/heroku@master</span></td>
</tr>
<tr class="even">
<td><span class="title-ref">{user}/{repo}/{path}@{ref}</span></td>
<td>A subdirectory in a public GitHub repository at a specific branch, ref, or SHA. <strong>Example</strong>: <span class="title-ref">actions/aws/ec2@v2.0.1</span></td>
</tr>
<tr class="odd">
<td><span class="title-ref">./path/to/dir</span></td>
<td>The path to the directory that contains the action in your workflow's repository. <strong>Example</strong>: <span class="title-ref">./.github/action/my-action</span></td>
</tr>
<tr class="even">
<td><span class="title-ref">docker://{image}:{tag}</span></td>
<td>A Docker image published on Docker Hub. <strong>Example</strong>: <span class="title-ref">docker://alpine:3.8</span></td>
</tr>
<tr class="odd">
<td><span class="title-ref">docker://{host}/{image}:{tag}</span></td>
<td>A Docker image in a public registry. <strong>Example</strong>: <span class="title-ref">docker://gcr.io/cloud-builders/gradle</span></td>
</tr>
</tbody>
</table>

In the case of the first two options (where an action references a 
public repository), Popper extends the syntax in the following way:

```
`{url}/{user}/{repo}/{path}@{ref}`
```

The `{url}` can reference any Git repository, allowing workflows to 
reference to actions outside of Github. For example:

```
action "myaction on gitlab" {
  uses = "git@gitlab.com:user/repo/path/to/my/action@master"
}

action "another one on bitbucket" {
  uses = "https://bitbucket.com/user/repo/action@master"
}
```

the above references actions hosted on [Gitlab](https://gitlab.com) 
and [Bitbucket](https://bitbucket.org).

## Other Runtimes

By default, actions in Popper workflows run in Docker, similarly to 
how they run in the Github Actions platform. Popper adds the ability 
of running actions in other runtimes by extending the interpretation 
of the `uses` attribute of action blocks.

> **NOTE**: As part of our roadmap, we plan to add support for Vagrant 
> and Conda runtimes. Open a [new 
> issue](https://github.com/systemslab/popper/issues/new) to request 
> another runtime you would Popper to support.

### Singularity

> **NOTE**: This feature requires Singularity 2.6+ to be installed.

An action executes in a Singularity container when:

  * A singularity image is referenced. For example: `shub://myimage` 
    will pull the container from the [singularity 
    hub](https://singularity-hub.org).

  * A `singularity.def` file is found in the action folder. For 
    example, if `./actions/mycontainer` is the value of the `uses` 
    attribute in an action block, and a `singularity.def` is found, 
    Popper builds and executes a singularity container.

  * A `singularity.def` is found in the public repository of the given 
    action. If an action resides in a public Git repository, and the 
    path to the action contains a `singularity.def` file, it will get 
    executed in Singularity.

### Host

Actions can execute directly on the host where the `popper` command is 
running. This happens when no `Dockerfile` or `Singularity` file is 
found in the path where the referenced action is stored (be it a local 
path or the path in a public repository). Popper looks for an 
`entrypoint.sh` file and executes it if found, otherwise an error is 
thrown. Alternatively, if the action block specifies a `runs` 
attribute, the script corresponding to it is executed. For example:

```hcl
action "run on host" {
  uses = "./myactions/onhost"
}

action "another execution on host" {
  uses = "./myactions/onhost"
  runs = "myscript"
}
```

In the above example, the `run on host` action is executed by looking 
for an `entrypoint.sh` file on the `./myactions/onhost/` folder. The 
`another execution on host` action will instead execute the `myscript` 
folder. Another way of executing actions on the host is to use the 
special `sh` value for the `uses` attribute. For example:

```hcl
action "run on host" {
  uses = "sh"
  runs = "ls -la"
}
```

The above runs `ls` on the root of the repository folder (the 
repository storing the `.workflow` file). This option allows users to 
execute arbitrary commands or scripts contained in the repository 
without having to define an action folder. The downside of this 
approach is that, depending on the command being executed, the 
workflow might not be portable.

> **NOTE**: The working directory for actions that run on the host is 
> the root folder of the project. Thus, to ensure portability, scripts 
> should use paths relative to the root of the folder. If absolute 
> paths are needed, the `$GITHUB_WORKSPACE` variable can be used.

