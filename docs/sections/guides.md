# Guides

This is a list of guides related to several aspects of working with 
Github Action (GHA) workflows.

## Implementing a Workflow for an Existing Set of Scripts

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
