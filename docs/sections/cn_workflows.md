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
step. All attributes are optional with the exception of the `uses` 
attribute.

| Attribute   | Description |
| :---------  | :-------------------- |
| `uses`      | **required** A string with the name of the image that will be executed for that<br>step. For example, `uses: docker://node:10`. See **"Referencing<br>images in a step"** section below for more examples. |
| `id`        | **optional** Assigns an identifier to the step. By default, steps are assigned a<br>numeric ID corresponding to the order of the step in the list, with<br>`'1'` identifying the first step. |
| `runs`      | **optional** A list of strings that specifies the command to run in the container.<br>If `runs` is omitted, the command specified in the `Dockerfile`'s<br>`ENTRYPOINT` instruction will execute. Use the `runs` attribute<br>when the `Dockerfile` does not specify an `ENTRYPOINT` or you want<br>to override the `ENTRYPOINT` command. The `runs` attribute does<br>not invoke a shell by default. Using `runs: "echo $VAR"` will<br>**NOT** print the value stored in `$VAR`, but will instead print<br>`\"\$VAR.\"`. To use environment variables with the `runs`<br>instruction, you must include a shell to expand the variables, for<br>example: `runs: ["sh", "-c", "echo $VAR"]`.  If the value of<br>`runs` refers to a local script, the path is relative to the<br>workspace folder (see [The Workspace](#the-workspace) section<br>below). |
| `args`      | **optional** A list of strings representing the arguments to pass to the command.<br>For example, `args: ["--flag", "--arg", "value"]`. If the value of<br>`args` refers to a local script, the path is relative to the workspace<br>folder (see [The Workspace](#the-workspace) section below). Similarly<br>to the `runs` attribute, if an environment variable is being<br>referenced, in order for this reference to be valid, a shell must be<br>invoked (in the `runs` attribute) in order to expand the value of the<br>variable. |
| `env`       | **optional** A dictionary of environment variables to set inside the container's<br>runtime environment. For example: `env: {VAR1: FOO, VAR2: bar}`. In<br>order to access these environment variables from a script that runs<br>inside the container, make sure the script runs a shell (e.g. `bash`)<br>in order to perform variable substitution. |
| `secrets`   | **optional** A list of strings representing the names of secret variables to define<br>in the environment of the container for the step. For example,<br>`secrets: ["SECRET1", "SECRET2"]`. |
| `skip_pull` | **optional** A boolean value that determines whether to pull the image before<br>executing the step. By default this is `false`. If the given container<br>image already exist (e.g. because it was built by a previous step in<br>the same workflow), assigning `true` skips downloading the image from<br>the registry. |
| `dir`       | **optional** A string representing an absolute path inside the container to use as the<br>working directory. By default, this is `/workspace`. |
| `options`   | **optional** Container configuration options. For instance:<br>`options: {ports: {8888:8888}, interactive: True, tty: True}`. Currently only<br> supported for the docker runtime. See the parameters of `client.containers.runs()`<br> in the [Docker Python SDK](https://docker-py.readthedocs.io/en/stable/containers.html?highlight=inspect) for the full list of options |

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
| `./path/to/dir`                    | The path to the directory that contains the `Dockerfile`. This is<br>a relative path with respect to the workspace directory (see<br>[The Workspace](#the-workspace) section below). **Example:** `./path/to/myimg/`. |
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
filesystem namespace of the host (the machine where `popper run` is 
executing) and the filesystem namespace within container:

```
                                 Container
                                +----------------------+
                                |  /bin                |
                                |  /etc                |
                                |  /lib                |
 Host                           |  /root               |
+-------------------+   bind    |  /sys                |
|                   |   mount   |  /tmp                |
| /home/me/my/proj <------+     |  /usr                |
| ├─ wf.yml         |     |     |  /var                |
| └─ README.md      |     +------> /workspace          |
|                   |           |  ├── wf.yml          |
|                   |           |  └── README.md       |
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
`/home/me/my/proj/`, we can run it by first changing the current 
working directory to this folder:

```bash
cd /home/me/my/proj/
popper run -f wf.yml
```

[touch_cmd]: https://en.wikipedia.org/wiki/Touch_(command)

And this will result in having a new file in `/home/me/my/proj/myfile`. 
However, if we invoke the workflow from a different folder, the folder 
being bind-mounted inside the container is a different one. For 
example:

```bash
cd /home/me/
popper run -f /home/me/my/proj/wf.yml
```

In the above, the file will be written to `/home/me/myfile`, because 
we are invoking the command from `/home/me/`, and this path is treated 
as the workspace folder. If we provide a value for the `--workspace` 
flag (or its short version `-w`), the workspace path then changes and 
thus the file is written to this given location. For example:

```bash
cd /
popper run -f /home/me/my/proj/wf.yml -w /home/me/my/proj/
```

The above writes the `/home/me/my/proj/myfile` even though Popper is 
being invoked from `/`. Note that the above is equivalent to the first 
example of this subsection, where we first changed the directory to 
`/home/me/my/proj` and ran `popper run -f wf.yml`.

### Changing the working directory

To specify a working directory for a step, you can use the `dir` 
attribute in the workflow, which takes as value a string representing 
an absolute path inside the container. This changes where the 
specified command is executed. For example, adding `dir` as follows:

```yaml
steps:
- uses: docker://alpine:3.9
  args: [touch, ./myfile]
  dir: /tmp/
```

And assuming that it is stored in `/home/me/my/proj/wf.yml`, invoking 
the workflow as:

```bash
cd /home/me
popper run -f wf.yml -w /home/me/my/proj
```

Would result in writing `myfile` in the `/tmp` folder that is 
**inside** the container filesystem namespace, as opposed to writing 
it to `/home/me/my/projc/` (the value given for the `--workspace` 
flag). As it is evident in this example, if the directory specified in 
the `dir` attribute resides outside the `/workspace` folder, then 
anything that gets written to it won't persist after the step ends its 
execution (see "Filesystem namespaces and persistence" below for 
more).

For completeness, we show an example of using `dir` to specify a 
folder within the workspace:

```yaml
steps:
- uses: docker://alpine:3.9
  args: [touch, ./myfile]
  dir: /workspace/my/proj/
```

And executing:

```bash
cd /home/me
popper run -f wf.yml
```

would result in having a file in `/home/me/my/proj/myfile`.

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
on resource managers such as SLURM and Kubernetes.

To run workflows on other container engines, an `--engine <engine>` 
flag for the `popper run` command can be given, where `<engine>` is 
one of the supported ones. When no value for this flag is given, 
Popper executes workflows in Docker. Below we briefly describe each 
container engine supported, and lastly describe how to pass 
engine-specific configuration options via the `--conf` flag.

### Docker

Docker is the default engine used by the `popper run`. All the 
container configuration for the docker engine is supported by Popper.
Popper also supports running workflows on remote docker daemons by use 
of the `DOCKER_HOST`, `DOCKER_TLS_VERIFY` and `DOCKER_CERT_PATH` 
variables, as explained in [the official 
documentation][docker-remote]. For example:

```bash
export DOCKER_HOST="ssh://myuser@hostname"
popper run -f wf.yml
```

The above runs the workflow on the `hostname` machine instead of 
locally. It assumes the following:

 1. `myuser` has passwordless access to `hostname`, otherwise the 
    password to the machine is requested.
 2. The `myuser` account can run `docker` on the remote machine.

[docker-remote]: https://docs.docker.com/engine/reference/commandline/dockerd

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

There are situations when executing a command directly on the host where the `popper` 
command is running. This is done by making use of the special `sh` 
value for the `uses` attribute. This value instructs Popper to execute 
the command or script given in the `runs` attribute directly on the host. For example:

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

[engconf]: ./cli_features#customizing-container-engine-behavior


Alternatively, to restrict a configuration to a specific step in a workflow, set the desired parameters in the step's `options`
**Note**: this is currently only supported for the Docker runtime 

## Resource Managers

By default, workflows are executed locally on the host where Popper is executed from.
In addition, workflows can also be executed through other resource managers.
The resource manager can be specified either through the `--resource-manager/-r` option, or specified in the configuration file given via the `--config/-c` flag.
If neither of them are provided, the steps are run in the host machine by default. 

### Kubernetes

Popper enables leveraging the compute and storage capabilities of the cloud by allowing running workflows on Kubernetes clusters. 
Users need to have access to a [cluster config file](https://v1-18.docs.kubernetes.io/docs/tasks/access-application-cluster/configure-access-multiple-clusters/) in order to run workflows on Kubernetes.
This file can be provided by a system administrator.

Popper provisions all the required resources and orchestrates the entire workflow execution.
When a workflow is executed, Popper first creates a persistent volume claim, spawns an init pod and uses it to copy the workflow context (packed in the form of a `.tar.gz` file) into the persistent volume and then unpacks the context there.
Subsequently, Popper tears down the init pod and executes the steps of a workflow in separate pods of their own.
After the execution of each step, the respective pods are deleted but the persistent volume claim is not deleted so that it can be reused by subsequent workflow executions.

For running workflows on Kubernetes, several configuration options can be passed to the Kubernetes resource manager through the Popper configuration file to customize the execution environment.
All the available configuration options have been described below:

* `namespace`: The namespace within which to provision resources like PVCs and Pods for workflow execution. If not provided the `default` namespace will be used.

* `persistent_volume_name`: Any pre-provisioned persistent volume like an NFS or EBS volume can be supplied through this option. Popper will then claim storage space from the supplied persistent volume. In the default case, a HostPath persistent volume of 1GB with a name of the form `pv-hostpath-popper-<workflowid>` will be created by Popper automatically.

* `volume_size`: The amount of storage space to claim from a persistent volume for use by a workflow. The default is 500MB.

* `pod_host_node`: The node on which to restrict the deployment of all the pods. 
  This option is important when a HostPath persistent volume is used. 
  In this case, users need to restrict all the pods to a particular node. 
  If this option is not provided, Popper will leave the task of scheduling the pods upon Kubernetes. 
  The exception to this is, when both the `pod_host_node` and `persistent_volume_name` options are not provided, Popper will try to find out a pod and schedule all the pods (init-pods + step-pods) on that node to use the `HostPath` persistent volume of 1GB which will be automatically created.

* `hostpathvol_path`: The path to use for creating a HostPath volume. If not provided, /tmp will be used.

* `hostpathvol_size`: The size of the HostPath volume. If not provided, 1GB will be used.

To run workflows on Kubernetes:

```bash
$ popper run -f wf.yml -r kubernetes
```

#### Limitations

  * A workflow cannot build local Dockerfiles. In order to work 
    around this issue, a workflow can build an image using BuildKit or 
    Kaniko as explained [here](./guides.html#building-images-using-buildkit).

### SLURM

Popper workflows can run on [HPC](https://en.wikipedia.org/wiki/HPC) (Multi-Node environments) 
using [Slurm](https://slurm.schedmd.com/overview.html) as the underlying resource manager to distribute the execution of a step to
several nodes. You can get started with running Popper workflows through Slurm by following the example below.

**NOTE:** Set the `POPPER_CACHE_DIR` environment variable to `/path/to/shared/.cache` while running a workflow on multiple nodes. 

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

To run all the steps of the workflow through SLURM resource manager,
use the `--resource-manager` or `-r` option of the `popper run` subcommand to specify the resource manager.

```bash
popper run -f sample.yml -r slurm
```

This runs the workflow on a single compute node in the cluster which is also the default scenario when no specific configuration is provided.

To have more finer control on which steps to run through SLURM resource manager,
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

This runs the step `one` locally in the host and step `two` through SLURM on any 2 compute nodes.
If `singularity` is used as the container engine, then by default the steps would run using MPI
as SLURM jobs. This behaviour can be overriden by passing `mpi: false` in the configuration of the
step for which MPI is not required.
