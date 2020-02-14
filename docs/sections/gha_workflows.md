
# Workflow Language and Runtime

This section introduces the [HCL-based][hcl] [workflow language][wfl] 
used by Popper and also describes the execution runtime.

> **NOTE**: The workflow language employed by Popper is **NOT** 
> supported by the official Github Actions platform. The HCL syntax 
> for workflows was [introduced by Github on 02/2019][parser] and 
> later [deprecated on 09/2019][drophcl]. The Popper project still 
> uses the HCL syntax.

[hcl]: https://github.com/hashicorp/hcl
[wfl]: https://en.wikipedia.org/wiki/Scientific_workflow_system
[parser]: https://github.blog/2019-02-07-an-open-source-parser-for-github-actions/
[drophcl]: https://github.blog/changelog/2019-09-17-github-actions-will-stop-running-workflows-written-in-hcl/

## Language

The following example workflow contains one workflow block and two 
action blocks.

```hcl
workflow "IDENTIFIER" {
  resolves = "ACTION2"
}

action "ACTION1" {
  uses = "docker://image1"
}

action "ACTION2" {
  needs = "ACTION1"
  uses = "docker://image2"
}
```

In this example, the workflow invokes `ACTION2` by inspecting the 
`resolves` attribute of the `workflow` block, but because `ACTION1` 
specifies that it `needs` to have `ACTION1` execute first, the 
`ACTION1` block is processed first (and so on and so forth until no 
more `needs` attributes are found). `ACTION2` will execute once 
`ACTION1` has successfully completed.

### Workflow blocks

A workflow file contains only one `workflow` block, containing the 
attributes outlined in the table shown below.

#### Workflow attributes

<table>
<thead>
<tr>
<th style="text-align:left">Name</th>
<th style="text-align:left">Description</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align:left"><code>resolves</code></td>
<td style="text-align:left">Identifies the action(s) to invoke. Can be a string or an array of strings. Any dependencies of the named action listed in the <code>needs</code> attribute of actions are also invoked. In the example workflow above, <code>ACTION2</code> runs first via the <code>resolves</code> attribute. When more than one action is listed, the actions are executed in parallel.</td>
</tr>
</tbody>
</table>

### Action blocks

A workflow file may contain any number of action blocks. Action blocks 
must have a unique identifier and must have a `uses` attribute. 
Example action block:

```hcl
action "IDENTIFIER" {
  needs = "ACTION1"
  uses = "docker://image2"
}
```

#### Action attributes

<table>
<thead>
<tr>
<th style="text-align:left">Name</th>
<th style="text-align:left">Description</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align:left"><code>needs</code></td>
<td style="text-align:left">Identifies actions that must complete successfully before this action will be invoked. It can be a string or an array of strings. In the example workflow above, <code>ACTION2</code> is executed after <code>ACTION1</code> is successfully completed. <strong>Note:</strong> When actions with a common <code>needs</code> dependency run in parallel and one action fails, the remaining actions are cancelled automatically.</td>
</tr>
<tr>
<td style="text-align:left"><code>uses</code></td>
<td style="text-align:left">The Docker image that will run the action. For example, <code>uses = &quot;node:10&quot;</code>. See &quot;Using a Dockerfile image in an action&quot; for more examples.</td>
</tr>
<tr>
<td style="text-align:left"><code>runs</code></td>
<td style="text-align:left">Specifies the command to run in the docker image. If <code>runs</code> is omitted, the command specified in the <code>Dockerfile</code>&#39;s <code>ENTRYPOINT</code> instruction will execute. Use the <code>runs</code> attribute when the <code>Dockerfile</code> does not specify an <code>ENTRYPOINT</code> or you want to override the <code>ENTRYPOINT</code> command. The <code>runs</code> attribute does not invoke a shell by default. To use environment variables with the <code>runs</code> instruction, you must include a shell to expand the variables, for example: <code>runs = [&quot;sh&quot;, &quot;-c&quot;, &quot;echo $GITHUB_SHA&quot;]</code>. Using <code>runs = &quot;echo $GITHUB_SHA&quot;</code> will not print the value stored in the <code>$GITHUB_SHA</code>, but will instead print <code>\&quot;\$GITHUB\_SHA.\&quot;</code></td>
</tr>
<tr>
<td style="text-align:left"><code>args</code></td>
<td style="text-align:left">The arguments to pass to the action. The <code>args</code> can be a string or array. If you provide <code>args</code> in a string, the string is split around whitespace. For example, <code>args = &quot;container:release --app web&quot;</code> or <code>args = [&quot;container:release&quot;, &quot;--app&quot;, &quot;web&quot;]</code>.</td>
</tr>
<tr>
<td style="text-align:left"><code>env</code></td>
<td style="text-align:left">The environment variables to set in the action&#39;s runtime environment. If you need to pass environment variables into an action, make sure your action runs a command shell to perform variable substitution. For example, if your <code>runs</code> attribute is set to <code>&quot;sh -c&quot;</code>, <code>args</code> will be run in a command shell. Alternatively, if your <code>Dockerfile</code> uses an <code>ENTRYPOINT</code> to run the same command (<code>&quot;sh -c&quot;</code>), <code>args</code> will execute in a command shell. See <a href="https://docs.docker.com/engine/reference/builder/#entrypoint"><code>ENTRYPOINT</code></a> for more details.</td>
</tr>
<tr>
<td style="text-align:left"><code>secrets</code></td>
<td style="text-align:left">Specifies the names of the secret variables to set in the runtime environment, which the action can access as an environment variable. For example, <code>secrets = [&quot;SECRET1&quot;, &quot;SECRET2&quot;]</code>.</td>
</tr>
</tbody>
</table>

<!--
| Name        | Description |
| :---------- | :-------------------- |
| `needs`     | Identifies actions that must complete successfully before this action will be invoked. It can be a string or an array of strings. In the example workflow above, `ACTION2` is executed after `ACTION1` is successfully completed. **Note:** When actions with a common `needs` dependency run in parallel and one action fails, the remaining actions are cancelled automatically. |
| `uses`      | The Docker image that will run the action. For example, `uses = "node:10"`. See "Using a Dockerfile image in an action" for more examples. |
| `runs`      | Specifies the command to run in the docker image. If `runs` is omitted, the command specified in the `Dockerfile`'s `ENTRYPOINT` instruction will execute. Use the `runs` attribute when the `Dockerfile` does not specify an `ENTRYPOINT` or you want to override the `ENTRYPOINT` command. The `runs` attribute does not invoke a shell by default. To use environment variables with the `runs` instruction, you must include a shell to expand the variables, for example: `runs = ["sh", "-c", "echo $GITHUB_SHA"]`. Using `runs = "echo $GITHUB_SHA"` will not print the value stored in the `$GITHUB_SHA`, but will instead print `\"\$GITHUB\_SHA.\"` |
| `args`      | The arguments to pass to the action. The `args` can be a string or array. If you provide `args` in a string, the string is split around whitespace. For example, `args = "container:release --app web"` or `args = ["container:release", "--app", "web"]`. |
| `env`       | The environment variables to set in the action's runtime environment. If you need to pass environment variables into an action, make sure your action runs a command shell to perform variable substitution. For example, if your `runs` attribute is set to `"sh -c"`, `args` will be run in a command shell. Alternatively, if your `Dockerfile` uses an `ENTRYPOINT` to run the same command (`"sh -c"`), `args` will execute in a command shell. See [`ENTRYPOINT`](https://docs.docker.com/engine/reference/builder/#entrypoint) for more details. |
| `secrets`   | Specifies the names of the secret variables to set in the runtime environment, which the action can access as an environment variable. For example, `secrets = ["SECRET1", "SECRET2"]`.
-->

### Using a `Dockerfile` image in an action

When creating an action block, you can use an action defined in the 
same repository as the workflow, a public repository, or in a 
[published Docker container image](https://hub.docker.com/). An action 
block refers to the images using the `uses` attribute. It's strongly 
recommended to include the version of the action you are using by 
specifying a SHA or Docker tag number. If you don't specify a version 
and the action owner publishes an update, it may break your workflows 
or have unexpected behavior. Here are some examples of how you can 
refer to an action on a public Git repository or Docker container registry:

<table>
<thead>
<tr>
<th style="text-align:left">Template</th>
<th style="text-align:left">Description</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align:left"><code>{url}/{user}/{repo}@{ref}</code></td>
<td style="text-align:left">A specific branch, ref, or SHA in a public Git repository. If <code>url</code> is ommited, <code>github.com</code> is used by default. <strong>Example:</strong>  <code>https://bitbucket.com/popperized/ansible@master</code>.</td>
</tr>
<tr>
<td style="text-align:left"><code>{url}/{user}/{repo}/{path}@{ref}</code></td>
<td style="text-align:left">A subdirectory in a public Git repository at a specific branch, ref, or SHA. <strong>Example:</strong> <code>git@gitlab.com:popperized/geni/build-context@v2.0</code></td>
</tr>
<tr>
<td style="text-align:left"><code>./path/to/dir</code></td>
<td style="text-align:left">The path to the directory that contains the action in your workflow&#39;s repository. <strong>Example:</strong> <code>./actions/my-action</code></td>
</tr>
<tr>
<td style="text-align:left"><code>docker://{image}:{tag}</code></td>
<td style="text-align:left">A Docker image published on <a href="https://hub.docker.com/">Docker Hub</a>. <strong>Example:</strong> <code>docker://alpine:3.8</code></td>
</tr>
<tr>
<td style="text-align:left"><code>docker://{host}/{image}:{tag}</code></td>
<td style="text-align:left">A Docker image in a public registry. <strong>Example:</strong> <code>docker://gcr.io/cloud-builders/gradle</code>.</td>
</tr>
</tbody>
</table>

<!--

| Template                           | Description |
| :--------------------------------- | :--------------------------------- |
| `{url}/{user}/{repo}@{ref}`        |  A specific branch, ref, or SHA in a public Git repository. If `url` is ommited, `github.com` is used by default. **Example:**  `https://bitbucket.com/popperized/ansible@master`. |
| `{url}/{user}/{repo}/{path}@{ref}` |  A subdirectory in a public Git repository at a specific branch, ref, or SHA. **Example:** `git@gitlab.com:popperized/geni/build-context@v2.0` |
| `./path/to/dir`                    |  The path to the directory that contains the action in your workflow's repository. **Example:** `./actions/my-action` |
| `docker://{image}:{tag}`           |  A Docker image published on [Docker Hub](https://hub.docker.com/). **Example:** `docker://alpine:3.8` |
| `docker://{host}/{image}:{tag}`    |  A Docker image in a public registry. **Example:** `docker://gcr.io/cloud-builders/gradle`. |

-->

### Referencing private Github repositories in an action

We can make use of actions located in private Github repositories by defining a ```GITHUB_API_TOKEN``` environment variable that the ```popper run``` command reads and uses to clone private Github repositories. To accomplish this, the repository referenced in the ```uses``` attribute is assumed to be private and, to access it, an API token from Github is needed (see instructions <a href = "https://github.com/settings/tokens">here</a>). The token needs to have permissions to read the private repository in question. To run a workflow that references private repositories:

```bash
export GITHUB_API_TOKEN=access_token_here
popper run
```

If the access token doesn't have permissions to access private repositories, the popper run command will fail.

## Execution Runtime

This section describes the runtime environment where a workflow 
executes.

### Environment variables

An action can create, read, and modify environment variables. When you 
create an action in a workflow, you can define environment variables 
using the `env` attribute in your action block. For example, you could 
set the variables `FIRST_NAME`, `MIDDLE_NAME`, and `LAST_NAME` using 
this example action block:

```hcl
action "hello world" {
  uses = "./my-action"
  env = {
    FIRST_NAME  = "Mona"
    MIDDLE_NAME = "Lisa"
    LAST_NAME   = "Octocat"
  }
}
```

When an action runs, Popper also sets these environment variables in 
the runtime environment:

<table>
<thead>
<tr>
<th style="text-align:left">Environment variable</th>
<th style="text-align:left">Description</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align:left"><code>HOME</code></td>
<td style="text-align:left">The path to the home directory used to store user data. Value: <code>/github/home</code>.</td>
</tr>
<tr>
<td style="text-align:left"><code>GITHUB_WORKFLOW</code></td>
<td style="text-align:left">The name of the workflow.</td>
</tr>
<tr>
<td style="text-align:left"><code>GITHUB_ACTION</code></td>
<td style="text-align:left">The name of the action.</td>
</tr>
<tr>
<td style="text-align:left"><code>GITHUB_ACTOR</code></td>
<td style="text-align:left">The name of the person or app that initiated the workflow. For example, <code>octocat</code>.</td>
</tr>
<tr>
<td style="text-align:left"><code>GITHUB_REPOSITORY</code></td>
<td style="text-align:left">The owner and repository name. For example, <code>octocat/Hello-World</code>.</td>
</tr>
<tr>
<td style="text-align:left"><code>GITHUB_WORKSPACE</code></td>
<td style="text-align:left">The workspace path. Value: <code>/github/workspace</code>. <strong>Note:</strong> actions must be run by the default Docker user (root). Ensure your Dockerfile does not set the <code>USER</code> instruction, otherwise you will not be able to access <code>GITHUB_WORKSPACE</code>.</td>
</tr>
<tr>
<td style="text-align:left"><code>GITHUB_SHA</code></td>
<td style="text-align:left">The commit SHA that triggered the workflow.</td>
</tr>
<tr>
<td style="text-align:left"><code>GITHUB_REF</code></td>
<td style="text-align:left">The branch or tag ref that triggered the workflow. For example, <code>refs/heads/feature-branch-1</code>. If neither a branch or tag is available for the event type, the variable will not exist.</td>
</tr>
</tbody>
</table>

<!--

| Environment variable   | Description |
| :--------------------- | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `HOME`                 | The path to the home directory used. Value: `/github/home`. |
| `GITHUB_WORKFLOW`      | The name of the workflow. |
| `GITHUB_ACTION`        | The name of the action. |
| `GITHUB_ACTOR`         | The name of the person or app that initiated the workflow. For example, `octocat`. |
| `GITHUB_REPOSITORY`    | The owner and repository name. For example, `octocat/Hello-World`. |
| `GITHUB_WORKSPACE`     | The workspace path. Value: `/github/workspace`. **Note:** actions must be run by the default Docker user (root). Ensure your Dockerfile does not set the `USER` instruction, otherwise you will not be able to access `GITHUB_WORKSPACE`. |
| `GITHUB_SHA`           | The commit SHA that triggered the workflow. |
| `GITHUB_REF`           | The branch or tag ref that triggered the workflow. For example, `refs/heads/feature-branch-1`. If neither a branch or tag is available for the event type, the variable will not exist. |

-->

### Naming conventions

Any new environment variables you set that point to a location on the
file system should have a `_PATH` suffix. The `HOME` and
`GITHUB_WORKSPACE` default variables are exceptions to this convention
because the words \"home\" and \"workspace\" already imply a location.

### Filesystem

Two directories are bind-mounted on the `/github` path prefix. These two directories are shared from the host machine to the containers running in a workflow:

<table>
<thead>
<tr>
<th style="text-align:left">Directory</th>
<th style="text-align:left">Description</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align:left"><code>/github/home</code></td>
<td style="text-align:left">The <code>HOME</code> directory for the user running the workflow. This directory path is set in the <code>HOME</code> environment variable.</td>
</tr>
<tr>
<td style="text-align:left"><code>/github/workspace</code></td>
<td style="text-align:left">The working directory of the Docker container. Actions execute in this directory. The path to this directory is set in the <code>GITHUB_WORKSPACE</code> environment variable. This directory is where the repository (with version <code>GITHUB_SHA</code>) that triggered the workflow. An action can modify the contents of this directory, which subsequent actions can access. <strong>Note:</strong> actions must be run by the default Docker user (root). Ensure your Dockerfile does not set the <a href="https://docs.docker.com/engine/reference/builder/#user"><code>USER</code> instruction</a>, otherwise you will not be able to access <code>GITHUB_WORKSPACE</code>.</td>
</tr>
</tbody>
</table>

<!--

| Directory                       | Description |
| :------------------------------ | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `/github/home`                  | The `HOME` directory for the user running the workflow. This directory path is set in the `HOME` environment variable. |
| `/github/workspace`             | The working directory of the Docker container. Actions execute in this directory. The path to this directory is set in the `GITHUB_WORKSPACE` environment variable. This directory is where the repository (with version `GITHUB_SHA`) that triggered the workflow. An action can modify the contents of this directory, which subsequent actions can access. **Note:** actions must be run by the default Docker user (root). Ensure your Dockerfile does not set the [`USER` instruction](https://docs.docker.com/engine/reference/builder/#user), otherwise you will not be able to access `GITHUB_WORKSPACE`. |

-->

#### Exit codes and statuses

You can use exit codes to provide an action\'s status. Popper uses the 
exit code to set the workflow execution status, which can be 
`success`, `neutral`, or `failure`:

<table>
<thead>
<tr>
<th style="text-align:left">Exit status</th>
<th style="text-align:left">Check run status</th>
<th style="text-align:left">Description</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align:left"><code>0</code></td>
<td style="text-align:left"><code>success</code></td>
<td style="text-align:left">The action completed successfully and other tasks that depends on it can begin.</td>
</tr>
<tr>
<td style="text-align:left"><code>78</code></td>
<td style="text-align:left"><code>neutral</code></td>
<td style="text-align:left">The configuration error exit status (<a href="https://github.com/freebsd/freebsd/blob/6c262608dd9129e8699bd3c3a84425b8076b83ae/include/sysexits.h#L114"><code>EX_CONFIG</code></a>) indicates that the action terminated but did not fail. For example, a <a href="https://github.com/popperized/bin/tree/master/filter">filter action</a> can use a <code>neutral</code> status to stop a workflow if certain conditions aren\&#39;t met. When an action returns this exit status, Popper terminates all concurrently running actions and prevents any future actions from starting. The associated check run shows a <code>neutral</code> status, and the overall check suite will have a status of <code>success</code> as long as there were no failed or cancelled actions.</td>
</tr>
<tr>
<td style="text-align:left">All other codes</td>
<td style="text-align:left"><code>failure</code></td>
<td style="text-align:left">Any other exit code indicates the action failed. When an action fails, all concurrent actions are cancelled and future actions are skipped. The check run and check suite both get a <code>failure</code> status.</td>
</tr>
</tbody>
</table>

<!--

| Exit status       | Check run status   | Description |
| :---------------- | :----------------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `0`               | `success`          | The action completed successfully and other tasks that depends on it can begin. |
| `78`              | `neutral`          | The configuration error exit status ([`EX_CONFIG`](https://github.com/freebsd/freebsd/blob/6c262608dd9129e8699bd3c3a84425b8076b83ae/include/sysexits.h#L114)) indicates that the action terminated but did not fail. For example, a [filter action](https://github.com/popperized/bin/tree/master/filter) can use a `neutral` status to stop a workflow if certain conditions aren\'t met. When an action returns this exit status, Popper terminates all concurrently running actions and prevents any future actions from starting. The associated check run shows a `neutral` status, and the overall check suite will have a status of `success` as long as there were no failed or cancelled actions. |
| All other codes   | `failure`          | Any other exit code indicates the action failed. When an action fails, all concurrent actions are cancelled and future actions are skipped. The check run and check suite both get a `failure` status. |

-->

### Alternative container engines

By default, actions in Popper workflows run in Docker. In addition to 
Docker, Popper can execute workflows in other runtimes by interacting 
with other container engines. A `--engine <engine>` flag for the 
`popper run` can be used to invoke alternative engines (where 
`<engine>` is one of the supported engines). When no value for the 
`--engine` option is given, Popper executes workflows in Docker.

> **NOTE**: As part of our roadmap, we plan to add support for the 
> [Podman](https://podman.io/) runtime. Open a [new
> issue](https://github.com/systemslab/popper/issues/new) to request 
> another runtime you would want Popper to support.

#### Singularity

Popper can execute a workflow in systems where Singularity 3.2+ is 
available. To execute a workflow in Singularity containers:

```bash
popper run --engine singularity
```

##### Limitations

  * The use of `ARG` in `Dockerfile`s is not supported by Singularity.
  * Currently, the `--reuse` functionality of the `popper run` command 
    is not available when running in Singularity.

#### Vagrant

While technically not a container engine, executing workflows inside a 
VM allows users to run workflows in machines where a container engine 
is not available. In this scenario, Popper uses [Vagrant][vagrant] to 
spawn a VM provisioned with Docker. It then executes workflows by 
communicating with the Docker daemon that runs inside the VM. To 
execute a workflow in Vagrant:

```bash
popper run --engine vagrant
```

[vagrant]: https://vagrantup.com/

##### Limitations

Currently, only one workflow can be executed at the time in Vagrant 
runtime, since popper assumes that there is only one VM running at any 
given point in time.

#### Host

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
