# Extensions

This section describes the extensions Popper brings on top of Github 
Actions.

> **NOTE**: These extensions are NOT supported by the official Github 
> runner.

## Reference Actions From Arbitrary Git Repositories

The syntax for defining actions in a workflow is the following:

```hcl
action "IDENTIFIER" {
  needs = "ACTION1"
  uses = "docker://image2"
}
```

Other optional [action block 
attributes](https://developer.github.com/actions/managing-workflows/workflow-configuration-options/#using-a-dockerfile-image-in-an-action) 
can be specified. The `uses` attribute references Docker images or 
Docker image definitions, i.e. `Dockerfile`s. The syntax for the 
`uses` attribute is the following:

```eval_rst
+---------------------------------+-----------------------------------------------------------------------------------------------------------------------------+
| Template                        | Description                                                                                                                 |
+=================================+=============================================================================================================================+
| `{user}/{repo}@{ref}`           | A specific branch, ref, or SHA in a public GitHub repository. **Example**: `actions/heroku@master`                          |
+---------------------------------+-----------------------------------------------------------------------------------------------------------------------------+
| `{user}/{repo}/{path}@{ref}`    | A subdirectory in a public GitHub repository at a specific branch, ref, or SHA. **Example**: `actions/aws/ec2@v2.0.1`       |
+---------------------------------+-----------------------------------------------------------------------------------------------------------------------------+
| `./path/to/dir`                 | The path to the directory that contains the action in your workflow's repository. **Example**: `./.github/action/my-action` |
+---------------------------------+-----------------------------------------------------------------------------------------------------------------------------+
| `docker://{image}:{tag}`        | A Docker image published on Docker Hub. **Example**: `docker://alpine:3.8`                                                  |
+---------------------------------+-----------------------------------------------------------------------------------------------------------------------------+
| `docker://{host}/{image}:{tag}` | A Docker image in a public registry. **Example**: `docker://gcr.io/cloud-builders/gradle`                                   |
+---------------------------------+-----------------------------------------------------------------------------------------------------------------------------+
```


## Other Runtimes

By default, actions in Popper workflows run in Docker, similarly to 
how they run in Github Actions.

> **NOTE**: As part of our roadmap, we plan to add support for Vagrant 
> and Conda runtimes. Open a [new 
> issue](https://github.com/systemslab/popper/issues/new) to request 
> another runtime you would Popper to support.

### Host

### Singularity

## Environment Variables

