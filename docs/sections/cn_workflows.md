# Workflow Syntax and Execution Runtime

This section introduces the YAML syntax used by Popper, describes the 
workflow execution runtime and shows how to execute workflows in 
alternative container engines.

## Syntax

A Popper workflow file looks like the following:

```yaml
steps:
- uses: docker://alpine:3.9
  args: ["ls", "-la"]

- uses: docker://alpine:3.11
  args: ["echo", "second step"]

options:
  env:
    FOO: BAR
  secrets:
  - TOP_SECRET
```

A workflow specification contains one or more steps in the form of a 
YAML list named `steps`. Each item in the list is a dictionary 
containing at least a `uses` attribute, which determines the docker 
image being used for that step. An `options` dictionary specifies 
options that are applied to the workflow.

### Workflow steps

The following table describes the attributes that can be used for a 
step. All attributes are optional with the exception of the `uses` attribute.

| Attribute   | Description |
| :---------  | :-------------------- |
| `uses`      | **required** The Docker image that will be executed for that step. For example,<br>`uses: docker://node:10`. See **"Referencing images in a step"** section below for<br>more examples. |
| `id`        | **optional** Assigns an identifier to the step. By default, steps are asigned a numerid id<br>corresponding to the order of the step in the list, with `1` identifying<br>the first step. |
| `runs`      | **optional** Specifies the command to run in the docker image. If `runs` is omitted, the<br>command specified in the `Dockerfile`'s `ENTRYPOINT` instruction will execute.<br>Use the `runs` attribute when the `Dockerfile` does not specify an `ENTRYPOINT`<br>or you want to override the `ENTRYPOINT` command. The `runs` attribute does not<br>invoke a shell by default. Using `runs: "echo $VAR"` will not print the value<br>stored in `$VAR`, but will instead print `\"\$VAR.\"`. To use environment<br>variables with the `runs` instruction, you must include a shell to expand<br>the variables, for example: `runs: ["sh", "-c", "echo $VAR"]`.  If the value of `runs`<br>refers to a local script, the path is relative to the workspace folder (see<br>[The Workspace](#the-workspace) section below)|
| `args`      | **optional** The arguments to pass to the command. This is an array of strings. For example,<br> `args: ["--flag", "--arg", "value"]`. If the value of `args`<br>refers to a local script, the path is relative to the workspace folder (see<br>[The Workspace](#the-workspace) section below). Similarly to the `runs` attribute, if an envrionment variable is being<br>referenced, in order for this reference to be valid, a shell must be invoked (in the `runs` attribute)<br>in order to expand the value of the variable. |
| `env`       | **optional** The environment variables to set inside the container's runtime environment. If<br>you need to pass environment variables into a step, make sure it runs a command<br>shell to perform variable substitution. For example, if your `runs` attribute is<br>set to `["sh", "-c"]`, the value of `args` will be passed to `sh -c` and<br>executed in a command shell. Alternatively, if your `Dockerfile` uses an<br>`ENTRYPOINT` to run the same command (`"sh -c"`), `args` will execute in a<br>command shell as well. See [`ENTRYPOINT`](https://docs.docker.com/engine/reference/builder/#entrypoint) for more details. |
| `secrets`   | **optional** Specifies the names of the secret variables to set in the runtime environment<br>which the container can access as an environment variable. For example,<br>`secrets: ["SECRET1", "SECRET2"]`. |
| `skip_pull` | **optional** Assume that the given container image already exist and skip pulling it. |
| `dir`       | **optional** Specifies the working directory for a step. By default, the directory is always `/workspace` if another one is not defined. |
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
| `./path/to/dir`                    | The path to the directory that contains the `Dockerfile`. This is a relative<br>path with respect to the workspace directory (see<br>[The Workspace](#the-workspace) section below). **Example:** `./path/to/myimg/`. |
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
    [The Workspace](#the-workspace) section below).
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

### Workflow options

The `options` attribute can be used to specify `env` and `secrets` 
that are available to all the steps in the workflow. For example:

```yaml
options:
  env:
    FOO: var1
    BAR: var2
  secrets: [SECRET1, SECRET2]

steps:
- uses: docker://alpine:3.11
  runs: sh
  args: ["-c", "echo $FOO $SECRET1"]

- uses: docker://alpine:3.11
  runs: sh
  args: ["-c", "echo $ONLY_FOR"]
  env:
    ONLY_FOR: this step
```

The above shows environment variables that are available to all steps 
that get defined in the `options` dictionary; it also shows an example 
of a variable that is available only to a single step (second step). 
This attribute is optional.

## Execution Runtime

This section describes the runtime environment where a workflow 
executes.

### The Workspace

When a step is executed, a folder in your machine is bind-mounted 
(shared) to the `/workspace` folder inside the associated container. 
By default, the folder being bind-mounted is `$PWD`, that is, the 
working directory from where `popper run` is being invoked from. If 
the `-w` (or `--workspace`) flag is given, then the value for this 
flag is used instead. See the [official Docker documentation][voldoc] 
for more information about how volumes work with containers.

[voldoc]: https://docs.docker.com/storage/volumes/

The following diagram illustrates this relationship between the 
filesystems of the host (machine where `popper run` is invoked) and 
the filesystem namespace within container:

```
                                Container
                                +----------------------+
                                |  /bin                |
                                |  /etc                |
Host                            |  /lib                |
+-------------------+           |  /root               |
|                   | bindmount |  /sys                |
| /home/user/proj <-------+     |  /tmp                |
| ├─ wf.yml         |     |     |  /var                |
| └─ README.md      |     +------> /workspace          |
|                   |           |  ├── wf.yml          |
|                   |           |  └── README.md       |
|                   |           |                      |
+-------------------+           +----------------------+
```

For example, let's look at a workflow that creates files in the 
workspace:

```yaml
steps:
- uses: docker://alpine:3.12
  args: [touch, ./myfile]
```

The above workflow has only one single step that creates the `myfile` 
file in the workspace directory if it doesn't exist, or updates its 
metadata if it already exists, using the [`touch` command][touch_cmd]. 
Assuming the above workflow is stored in a `wf.yml` file in 
`/home/user/proj/`, we can run it by first changing the current 
working directory to this folder:

```bash
cd /home/user/proj/
popper run -f wf.yml
```

[touch_cmd]: https://en.wikipedia.org/wiki/Touch_(command)

And this will result in having a new file in `/home/user/proj/myfile`. 
However, if we invoke the workflow from a different folder, the folder 
being bind-mounted inside the container is a different one. For 
example:

```bash
cd /tmp
popper run -f /home/user/proj/wf.yml
```

In the above, the file will be written to `/tmp/myfile`. If we provide 
a value for `-w`, the workspace path then changes and thus the file is 
written to this given location. For example

```bash
cd /tmp
popper run -f /home/user/proj/wf.yml -w /home/user/proj/
```

The above writes the `/home/user/proj/myfile` even though Popper is 
being invoked from `/tmp`, since the `-w` flag is being passed to 
`popper run`.

### Changing the working directory

To specify a working directory for a step you can use the `dir` attribute
in the workflow. This going to change where the specified
command is executed.

For example, adding `dir` to a workflow results in the following:

```yaml
version: '1'
steps:
- uses: docker://alpine:3.9
  args: [touch, ./myfile]
  dir: /path/to/dir/
```

It is worth mentioning that if the directory is specified outside the
`/workspace` folder, then anything that gets written to it won't persist
(see below for more).

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

#### Git Variables

When Popper executes insides a git repository, it obtains information 
related to Git. These variables are prefixed with `GIT_` (e.g. to
`GIT_COMMIT` or `GIT_BRANCH`).

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

By default, Popper workflows run in Docker on the machine where 
`popper run` is being executed (i.e. the host machine). This section 
describes how to execute in other container engines. See [next 
section](#resource-managers) for information on how to run workflows 
on resource managers  such as SLURM and Kubernetes.

To run workflows on other container engines, an `--engine <engine>` 
flag for the `popper run` command can be given, where `<engine>` is 
one of the supported ones. When no value for this flag is given, 
Popper executes workflows in Docker. Below we briefly describe each 
container engine supported, and lastly describe how to pass 
engine-specific configuration options via the `--conf` flag.

### Docker

Docker is the default engine used by the `popper run`. All the 
container configuration for the docker engine is supported by Popper.

### Singularity

Popper can execute a workflow in systems where Singularity 3.2+ is 
available. To execute a workflow in Singularity containers:

```bash
popper run --engine singularity
```

#### Limitations

  * The use of `ARG` in `Dockerfile`s is not supported by Singularity.
  * The `--reuse` flag of the `popper run` command is not supported.

### Host

There are situations where a container runtime is not available and 
cannot be installed. In these cases, a step can be executed directly 
on the host, that is, on the same environment where the `popper` 
command is running. This is done by making use of the special `sh` 
value for the `uses` attribute. This value instructs Popper to execute 
the command or script given in the `runs` attribute. For example:

```yaml
steps:
- uses: "sh"
  runs: ["ls", "-la"]

- uses: "sh"
  runs: "./path/to/my/script.sh"
  args: ["some", "args", "to", "the", "script"]
```

In the first step above, the `ls -la` command is executed on the 
workspace folder (see ["The Workspace"](#the-workspace) section). The 
second one shows how to execute a script. Note that the command or 
script specified in the `runs` attribute are NOT executed in a shell. 
If you need a shell, you have to explicitly invoke one, for example:

```yaml
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

[engconf]: /cli_features#customizing-container-engine-behavior

## Resource Managers

Popper can execute steps in a workflow through other resource managers
like SLURM besides the host machine. The resource manager can be specified 
either through the `--resource-manager/-r` option or through the config file.
If neither of them are provided, the steps are run in the host machine 
by default. 

### SLURM

Popper workflows can run on [HPC](https://en.wikipedia.org/wiki/HPC) (Multi-Node environments) 
using [Slurm](https://slurm.schedmd.com/overview.html) as the underlying resource manager to distribute the execution of a step to
several nodes. You can get started with running Popper workflows through Slurm by following the example below.

Let's consider a workflow `sample.yml` like the one shown below.
```yaml
steps:
- id: one
  uses: docker://alpine:3.9
  args: ["echo", "hello-world"]

- id: two
  uses: popperized/bin/sh@master
  args: ["ls", "-l"]
```

To run all the steps of the workflow through slurm resource manager,
use the `--resource-manager` or `-r` option of the `popper run` subcommand to specify the resource manager.

```bash
popper run -f sample.yml -r slurm
```

To have more finer control on which steps to run through slurm resource manager,
the specifications can be provided through the config file as shown below.

We create a config file called `config.yml` with the following contents.

```yaml
engine:
  name: docker
  options:
    privileged: True
    hostname: example.local

resource_manager:
  name: slurm
  options:
    two:
      nodes: 2
```

Now, we execute `popper run` with this config file as follows:

```bash
popper run -f sample.yml -c config.yml
```

This runs the step `one` locally in the host and step `two` through slurm on 2 nodes.

#### Host

Popper executes the workflows by default using the `host` machine as the resource manager. So, when no resource manager is provided like the example below, the workflow runs on the local machine.

```bash
popper run -f sample.yml
```

The above assumes `docker` as the container engine and `host` as the resource manager to be
used.
