# CI features

Popper can be used to apply a CI service-agnostic approach to 
automating the execution of pipelines. The `popper ci` command 
[generates configuration files](other_resources.html#ci-setup) that a 
CI service reads in order to execute a pipeline. This section 
describes this functionality. For more information on how to link your 
project to a CI service and how to test locally, check 
[here](cli_features.html#continuously-validating-a-pipeline).

## Execution logic

When `popper run` is invoked, each pipeline is executed in 
alpha-numerical order. When a pipeline runs, each of the stages is 
executed in the order specified by the `--stages` flag of the `init` 
command; the `stages` command; or by manually editing the 
`.popper.yml` file.

The following is the list of high-level tasks that are executed when 
running an pipeline:

 1. If specified, check for environmental requirements. See 
    [here](cli_features.html#specifying-environment-requirements) for 
    more.

 2. For every pipeline, trigger an execution by sequentially invoking
    all the scripts for all the defined stages of the pipeline.

 3. After the pipeline finishes, if a `validate.sh` script is defined, 
    parse its output. This script should print to standard output one 
    line per validation, denoting whether a validation passed or not. 
    In general, the form for validation results is `[true|false] 
    <statement>`, for example:

    ```
    [true]  algorithm A outperforms B
    [false] network throughput is 2x the IO bandwidth
    ```

 4. Keep track of every pipeline and report their status.

There are three possible values for the status of a pipeline: `FAIL`, 
`SUCCESS` and `GOLD`. When a pipeline does not run to completion (i.e. 
one of the stages failed), the status of the pipeline is `FAIL`. When 
the pipeline status' is `GOLD`, the status of all validations is 
`true`. When all the stages of a pipeline run successfully but one or 
more validations fail (the status of one or more validations is 
`false`), the status of a pipeline is `SUCCESS`.

When multiple pipelines are executed, the lowest status among all the 
pipelines is reported by the `popper run` command, with `FAIL` being 
the lowest and `GOLD` the highest.

### Skipping stages

The `popper run` command has a `--skip` argument that can be used to 
execute a pipeline in multiple steps. So for example, assuming we have 
a pipeline with the following scripts: `setup`, `run`, `post-run` and 
`validate`, we can run:

```bash
popper run --skip post-run,validate
```

Which runs the first part (setup and execution). Then, later we can 
either manually check whether the `run` stage is done or automate this 
task in the `post-run` script. In either way, we would then run:

```bash
popper run --skip setup,run
```

and the above will just execute the second half of the pipeline.

### Specifying which pipelines to run

By default, the `run` subcommand will try to run all the pipelines in 
a project, unless the current working directory is the folder 
containing a pipeline. Alternatively, the `run` subcommand takes as 
argument the name of a pipeline. For example:

```bash
cd my-popper-repo
popper run
```

The above runs all the pipelines in a repository. While the following 
runs only the pipeline named `my-pipe`.

```bash
cd my-popper-repo
popper run my-pipe
```

or alternatively:

```bash
cd my-popper-repo
cd pipelines/my-pipe
popper run
```

### Specifying which pipelines to run via commit messages

The previous subsection applies when `popper run` is invoked directly 
on a shell. However, when a CI service executes a pipeline, it does so 
by invoking `popper run` on the CI server, without passing any 
arguments or flags, and thus we cannot specify which pipelines to 
execute or skip. To make this more flexible, the `ci` command provides 
the ability to control which pipelines are executed by looking for 
special keywords in commit messages.

The `popper:whitelist[<list>]` keyword can be used in a commit message 
to specify which pipelines to execute. For example:

```
An example commit message

This is a sample commit message that shows how we can request the 
execution of a particular pipeline.

popper:whitelist[my-pipe]
```

The above commit message specifies that the pipeline `my-pipe` is to 
be executed and any other pipeline will be skipped. A comma-separated 
list of pipeline names can be given in order to request the execution 
of more then one pipeline. A skip list is also supported with the 
`popper:skip[<list>]` keyword.

## Execution environments

By default, a pipeline runs on the same environment where the `popper` 
command is being executed. In certain cases, it is useful to run a 
pipeline on a different environment. Popper leverages Docker to 
accomplish this. For more on how to define and remove environments, 
see [here](cli_features.html#envs). For each environment, an output 
log folder is created. For example, the following pipeline 2-stage 
pipeline:

```
pipelines:
  my-pipe:
    path: pipelines/my-pipe
    envs:
    - host
    - debian-9
    stages:
    - one
    - two
```

Results in the logs folder in `pipelines/my-pipe/popper` to have the 
following structure:

```
$ tree pipelines/my-pipe/popper
pipelines/my-pipe/popper
├── debian-9
│   ├── popper_status
│   ├── one.sh.err
│   ├── one.sh.out
│   ├── two.sh.err
│   └── two.sh.out
└── host
    ├── popper_status
    ├── one.sh.err
    ├── one.sh.err
    ├── two.sh.err
    └── two.sh.out
```

That is, there is one folder for each distinct environment. The status 
of the pipeline reported by `popper run` is the lowest status from all 
the executions, with `FAIL` being the lowest and `GOLD` the highest.

### Specifying arguments for `docker run`

A Docker environment image is instantiated with the following command:

```bash
docker run --rm \
  --volume /path/to/project:/path/to/project \
  --workdir /path/to/project/path/to/pipeline \
  <environment-image>
    popper run <flags> <arg>
```

That is, the project folder is shared with the container, and the 
working directory is the pipeline folder. To specify other flags to 
the `docker run` command, the `--argument` flag of the `env` command 
can be used. For usage, type `popper env --help`.

## Parametrizing pipelines

A pipeline can be parametrized so that it can be executed multiple 
times, taking distinct parameters each time. Parameters are specified 
with the `parameters` subcommand. Parameters of a pipeline are given 
in the form of environment variables. For example, if a pipeline takes 
parameters `par1` and `par2`, the following can specify these, along 
with the respective values that each parameter takes:

```
popper parameters my-pipe --add par1=val1 --add par2=val2
```

This will cause the `.popper.yml` to look like the following:

```
pipelines:
  my-pipe:
    envs:
    - host
    stages:
    - one
    - two
    parameters:
    - { par1: val1, par2: val2 }
```

Each parameterization results in a dictionary of key-value pairs, 
where each item in the dictionary is an environment variable. A 
subsequent set of parameters can be added:

```
popper parameters my-pipe --add par1=val3 --add par2=val4
```

Which will result in the following:

```
pipelines:
  my-pipe:
    envs:
    - host
    stages:
    - one
    - two
    parameters:
    - par1: val1
      par2: val2
    - par1: val3
      par2: val4
```

Thus, the above results in executing this same pipeline two times, 
defining environment variables `par1` and `par2`, with these 2 sets of 
values. We refer to each execution in a parametrized pipeline as a 
_Job_. In this example we will have 2 jobs every time the pipeline 
runs.

When a parametrized pipeline is executed, a subfolder for each job is 
created. For example, the 2-job pipeline specified above results in 
the following folder structure:

```bash
$ tree pipelines/your-popper-pipeline/popper
pipelines/your-popper-pipeline/popper
└── host
    ├── 0
    │   ├── popper_status
    │   ├── one.sh.err
    │   ├── one.sh.out
    │   ├── two.sh.err
    │   └── two.sh.out
    └── 1
        ├── popper_status
        ├── one.sh.err
        ├── one.sh.out
        ├── two.sh.err
        └── two.sh.out
```

Subfolders are numbered, were each id corresponds to the position in 
the `parameters` list.

## Matrix Executions

Combining _Execution environments_ with _Parameters_ results in a 
bi-dimensional matrix of jobs. For example, the following pipeline:

```
pipelines:
  my-pipe:
    envs:
    - host
    stages:
    - one
    - two
    parameters:
    - par1: val1
      par2: val2
    - par1: val3
      par2: val4
```

results in the following folder structure:

```bash
$ tree pipelines/your-popper-pipeline/popper
pipelines/your-popper-pipeline/popper
├── debian-9
│   ├── 0
│   │   ├── popper_status
│   │   ├── one.sh.err
│   │   ├── one.sh.out
│   │   ├── two.sh.err
│   │   └── two.sh.out
│   └── 1
│       ├── popper_status
│       ├── one.sh.err
│       ├── one.sh.out
│       ├── two.sh.err
│       └── two.sh.out
└── host
    ├── 0
    │   ├── popper_status
    │   ├── one.sh.err
    │   ├── one.sh.out
    │   ├── two.sh.err
    │   └── two.sh.out
    └── 1
        ├── popper_status
        ├── one.sh.err
        ├── one.sh.out
        ├── two.sh.err
        └── two.sh.out
```

## Popper Badges

See [here](cli_features.html#popper-badges).
