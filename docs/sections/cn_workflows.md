# Workflow Syntax and Execution Runtime

This section introduces the YAML syntax used by Popper, describes the 
workflow execution runtime and shows how to execute workflows in 
alternative container engines.

> _**NOTE**: Popper also supports the [now-deprecated HCL 
> syntax][drophcl] that was introduced in the alpha version of [Github 
> Action Workflows][parser]. We strongly recommend the use of Popper's 
> own YAML syntax._

[parser]: https://github.blog/2019-02-07-an-open-source-parser-for-github-actions/
[drophcl]: https://github.blog/changelog/2019-09-17-github-actions-will-stop-running-workflows-written-in-hcl/

## Syntax

A Popper workflow file looks like the following:

```yaml
version: '1'
steps:
- uses: docker://alpine:3.9
  args: ["ls", "-la"]
```

A workflow specification contains one or more steps in the form of a 
YAML list named `steps`. Each item in the list is a dictionary 
containing at least a `uses` attribute, which determines the docker 
image being used for that step.

### Workflow steps

The following table describes the attributes that can be used for a 
step. All attributes are optional with the exception of the `uses` attribute.

| Attribute  | Description |
| :--------- | :-------------------- |
| `uses`     | The Docker image that will be executed for that step. For example,<br>`uses: docker://node:10`. See **"Referencing images in a step"** section below for more examples. |
| `runs`     | Specifies the command to run in the docker image. If `runs` is omitted, the<br>command specified in the `Dockerfile`'s `ENTRYPOINT` instruction will execute.<br>Use the `runs` attribute when the `Dockerfile` does not specify an `ENTRYPOINT`<br>or you want to override the `ENTRYPOINT` command. The `runs` attribute does not<br>invoke a shell by default. Using `runs: "echo $VAR"` will not print the value<br>stored in `$VAR`, but will instead print `\"\$VAR.\"`. To use environment<br>variables with the `runs` instruction, you must include a shell to expand<br>the variables, for example: `runs: ["sh", "-c", "echo $VAR"]`.  If the value of `runs`<br>refers to a local script, the path is relative to the workspace folder (see [The workspace](#the-workspace) section below)|
| `args`     | The arguments to pass to the command. This can be a string or array. If you<br>provide `args` in a string, the string is split around whitespace. For example,<br> `args: "--flag --arg value"` or `args: ["--flag", "--arg", "value"]`. If the value of `args`<br>refers to a local script, the path is relative to the workspace folder (see [The workspace](#the-workspace) section below). |
| `env`      | The environment variables to set inside the container's runtime environment. If<br>you need to pass environment variables into a step, make sure it runs a command<br>shell to perform variable substitution. For example, if your `runs` attribute is<br>set to `["sh", "-c"]`, the value of `args` will be passed to `sh -c` and<br>executed in a command shell. Alternatively, if your `Dockerfile` uses an<br>`ENTRYPOINT` to run the same command (`"sh -c"`), `args` will execute in a<br>command shell as well. See [`ENTRYPOINT`](https://docs.docker.com/engine/reference/builder/#entrypoint) for more details. |
| `secrets`  | Specifies the names of the secret variables to set in the runtime environment<br>which the container can access as an environment variable. For example,<br>`secrets: ["SECRET1", "SECRET2"]`. |
| `id`       | Assigns an identifier to the step. By default, steps are asigned a numerid id<br>corresponding to the order of the step in the list, with `1` identifying<br>the first step. |
| `needs`    | Identifies steps that must complete successfully before this step will be<br>invoked. It can be a string or an array of strings. |

### Referencing images in a step

A step in a workflow can reference a container image defined in a 
`Dockerfile` that is part of the same repository where the workflow 
file resides. In addition, it can also reference a `Dockerfile` 
contained in public Git repository. A third option is to directly 
reference an image published a in a container registry such as 
[DockerHub][dh]. Here are some examples of how you can refer to an 
image on a public Git repository or Docker container registry:

| Template                           | Description |
| :--------------------------------- | :--------------------------------- |
| `./path/to/dir`                    | The path to the directory that contains the `Dockerfile`. This is a relative<br>path with respect to the workspace directory (see [The workspace](#the-workspace) section below).<br>**Example:** `./path/to/myimg/`. |
| `{url}/{user}/{repo}@{ref}`        | A specific branch, ref, or SHA in a public Git repository. If `url`<br>is ommited, `github.com` is used by default.<br>**Example:** `https://bitbucket.com/popperized/ansible@master`. |
| `{url}/{user}/{repo}/{path}@{ref}` | A subdirectory in a public Git repository at a specific branch, ref,<br>or SHA.<br>**Example:** `git@gitlab.com:popperized/geni/build-context@v2.0`. |
| `docker://{image}:{tag}`           | A Docker image published on [Docker Hub](https://hub.docker.com/).<br>**Example:** `docker://alpine:3.8`. |
| `docker://{host}/{image}:{tag}`    | A Docker image in a public registry other than DockerHub. Note<br>that the container engine needs to have properly configured to<br>access the referenced registry in order to download from it.<br>**Example:** `docker://gcr.io/cloud-builders/gradle`.|

It's strongly recommended to include the version of the image you are 
using by specifying a SHA or Docker tag. If you don't specify a 
version and the image owner publishes an update, it may break your 
workflows or have unexpected behavior.

In general, any Docker image can be used in a Popper workflow, but 
keep in mind the following:

  * When the `runs` attribute for a step is used, the `ENTRYPOINT` of 
    the image is overridden.
  * The `WORKDIR` is overridden and `/workspace` is used instead (see 
    [The workspace](#the-workspace) section below).
  * The `ARG` instruction is not supported, thus building an image 
    from a `Dockerfile` (public or local) only uses its default value.
  * While it is possible to run containers that specify `USER` other 
    than root, doing so might cause unexpected behavior.

[dh]: https://hub.docker.com

### Referencing private Github repositories

You can reference Dockerfiles located in private Github 
repositories by defining a `GITHUB_API_TOKEN` environment variable 
that the `popper run` command reads and uses to clone private 
repositories. The repository referenced in the `uses` attribute is 
assumed to be private and, to access it, an API token from Github is 
needed (see instructions [here](https://github.com/settings/tokens)). 
The token needs to have permissions to read the private repository in 
question. To run a workflow that references private repositories:

```bash
export GITHUB_API_TOKEN=access_token_here
popper run -f wf.yml
```

If the access token doesn't have permissions to access private 
repositories, the `popper run` command will fail.

## Execution Runtime

This section describes the runtime environment where a workflow 
executes.

### The workspace

When a step is executed, a folder in your machine is bind-mounted 
(shared) to the `/workspace` folder inside the associated container. 
By default, the folder being bind-mounted is `$PWD`, that is, the 
working directory from where `popper run` is being invoked from. If 
the `-w` (or `--workspace`) flag is given, then the value for this 
flag is used instead.

For example, let's look at a workflow that writes to a `myfile` in the 
workspace:

```yaml
version: '1'
steps:
- uses: docker://alpine:3.9
  args: [touch, ./myfile]
```

Assuming the above is stored in a `wf.yml` file, the following writes 
to the current working directory:

```bash
cd /tmp
popper run -f /path/to/wf.yml
```

In the above, `/tmp/myfile` is created. If we provide a value for 
`-w`, the workspace path changes and thus the file is written to that 
location:

```bash
cd /tmp
popper run -f /path/to/wf.yml -w /path/to
```

The above writes the `/path/to/myfile`. And, for completeness, the 
above is equivalent to:

```bash
cd /path/to
popper run -f wf.yml
```

### Filesystem namespaces and persistence

As mentioned previously, for every step Popper bind-mounts (shares) a 
folder from the host (the workspace) into the `/workspace` folder in 
the container. Anything written to this folder persists. Conversely, 
anything that is NOT written in this folder will not persist after the 
workflow finishes, and the associated containers get destroyed.

### Environment variables

A step can define, read, and modify environment variables. A step 
defines environment variables using the `env` attribute. For example, 
you could set the variables `FIRST`, `MIDDLE`, and `LAST` using this:

```yaml
version: '1'
steps:
- uses: "docker://alpine:3.9"
  args: ["sh", "-c", "echo my name is: $FIRST $MIDDLE $LAST"]
  env:
    FIRST: "Jane"
    MIDDLE: "Charlotte"
    LAST: "Doe"
```

When the above step executes, Popper makes these variables available 
to the container and thus the above prints to the terminal:

```
my name is: Jane Charlotte Doe
```

Note that these variables are only visible to the step defining them 
and any modifications made by the code executed within the step are 
not persisted between steps (i.e. other steps do not see these 
modifications).

### Exit codes and statuses

Exit codes are used to communicate about a step\'s status. Popper uses 
the exit code to set the workflow execution status, which can be 
`success`, `neutral`, or `failure`:

| Exit code | Status    | Description |
| :---------| :---------| :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `0`       | `success` | The step completed successfully and other tasks that depends on it can begin. |
| `78`      | `neutral` | The configuration error exit status ([`EX_CONFIG`](https://github.com/freebsd/freebsd/blob/6c262608dd9129e8699bd3c3a84425b8076b83ae/include/sysexits.h#L114)) indicates that the step<br>terminated but did not fail. For example, a [filter step](https://github.com/popperized/bin/tree/master/filter) can use a `neutral` status<br>to stop a workflow if certain conditions aren't met. When a step<br>returns this exit status, Popper terminates all concurrently running steps and<br>prevents any future steps from starting. The associated check run shows a<br>`neutral` status, and the overall check suite will have a status of `success`<br>as long as there were no failed or cancelled steps. |
| All other | `failure` | Any other exit code indicates the step failed. When a step fails, all concurrent<br>steps are cancelled and future steps are skipped. The check run and<br>check suite both get a `failure` status. |

## Container Engines

By default, steps in Popper workflows run in Docker. In addition, 
Popper can execute workflows in other runtimes by interacting with 
their corresponding container engines. An `--engine <engine>` flag for 
the `popper run` is used to invoke alternative engines, where 
`<engine>` is one of the supported engines. When no value for this 
flag is given, Popper executes workflows in Docker. Below we briefly 
describe each container engine supported (besides Docker), and lastly 
describe how to customize their configuration.

### Supported engines

#### Singularity

Popper can execute a workflow in systems where Singularity 3.2+ is 
available. To execute a workflow in Singularity containers:

```bash
popper run --engine singularity
```

##### Limitations

  * The use of `ARG` in `Dockerfile`s is not supported by Singularity.
  * The `--reuse` flag of the `popper run` command is not supported.

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

Only one workflow can be executed at the time in Vagrant runtime, 
since popper assumes that there is only one VM running at any given 
point in time.

#### Host

There are situations where a container runtime is not available and 
cannot be installed. In these cases, a step can be executed directly 
on the host, that is, on the same environment where the `popper` 
command is running. This is done by making use of the special `sh` 
value for the `uses` attribute. This value instructs Popper to execute 
the command or script given in the `runs` attribute. For example:

```yaml
version: '1'
steps:
- uses: "sh"
  runs: ["ls", "-la"]

- uses: "sh"
  runs: "./path/to/my/script.sh"
  args: ["some", "args", "to", "the", "script"]
```

In the first step above, the `ls -la` command is executed on the 
workspace folder (see ["The workspace"](#the-workspace) section). The 
second one shows how to execute a script. Note that the command or 
script specified in the `runs` attribute are NOT executed in a shell. 
If you need a shell, you have to explicitly invoke one, for example:

```yaml
version: '1'
steps:
- uses: sh
  runs: [bash, -c, 'sleep 10 && true && exit 0']
```

The obvious downside of running a step on the host is that, depending 
on the command being executed, the workflow might not be portable.

### Custom engine configuration

Other than bind-mounting the `/workspace` folder, Popper runs 
containers with any default configuration provided by the underlying 
engine. However, a `--conf` flag is provided by the `popper run` 
command to specify custom options for the underlying engine in 
question (see [here][engconf] for more).

[engconfg]: /cli_features#customizing-container-engine-behavior
