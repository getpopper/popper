# Guides

This is a list of guides related to several aspects of working with 
Popper workflows.

### Choosing a location for your step

If you are developing a docker image for other people to use, we 
recommend keeping this image in its own repository instead of bundling
it with your repository-specific logic. This allows you to version, 
track, and release this image just like any other software. Storing a 
docker image in its own repository makes it easier for others to 
discover, narrows the scope of the code base for developers fixing 
issues and extending the image, and decouples the image's versioning 
from the versioning of other application code.

### Using shell scripts to define step logic

Shell scripts are a great way to write the code in steps. If you can 
write a step in under 100 lines of code and it doesn't require complex 
or multi-line command arguments, a shell script is a great tool for 
the job. When defining steps using a shell script, follow these 
guidelines:

-   Use a POSIX-standard shell when possible. Use the `#!/bin/sh`
    [shebang](https://en.wikipedia.org/wiki/Shebang_(Unix)) to use the
    system\'s default shell. By default, Ubuntu and Debian use the
    [dash](https://wiki.ubuntu.com/DashAsBinSh) shell, and Alpine uses
    the [ash](https://en.wikipedia.org/wiki/Almquist_shell) shell. Using
    the default shell requires you to avoid using bash or shell-specific
    features in your script.
-   Use `set -eu` in your shell script to avoid continuing when errors
    or undefined variables are present.

### Hello world step example

You can create a new step by adding a `Dockerfile` to the directory in 
your repository that contains your step code. This example creates a 
simple step that writes arguments to standard output (`stdout`). An 
step declared in a `main.workflow` would pass the arguments that this 
step writes to `stdout`. To learn more about the instructions used in 
the `Dockerfile`, check out the [official Docker 
documentation][howto-dockerfile]. The two files you need to create an 
step are shown below:

**./step/Dockerfile**

```Dockerfile
FROM debian:9.5-slim

ADD entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
```

**./step/entrypoint.sh**

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

This `echo`s the arguments you pass the step. For example, if you were 
to pass the arguments `"Hello World"`, you\'d see this output in the 
command shell:

```bash
Hello World
```

## Creating a Docker container

Check out the [official Docker documentation][howto-dockerfile].

[howto-dockerfile]: https://docs.docker.com/engine/reference/builder/

## Implementing a workflow for an existing set of scripts

This guide exemplifies how to define a Popper workflow for an existing 
set of scripts. Assume we have a project in a `myproject/` folder and 
a list of scripts within the `myproject/scripts/` folder, as shown 
below:

```bash
cd myproject/
ls -l scripts/

total 16
-rwxrwx---  1 user  staff   927B Jul 22 19:01 download-data.sh
-rwxrwx---  1 user  staff   827B Jul 22 19:01 get_mean_by_group.py
-rwxrwx---  1 user  staff   415B Jul 22 19:01 validate_output.py
```

A straight-forward workflow for wrapping the above is the following:

```yaml
- uses: docker://alpine:3.12
  runs: "/bin/bash"
  args: ["scripts/download-data.sh"]

- uses: docker://alpine:3.12
  args: ["./scripts/get_mean_by_group.py", "5"]

- uses: docker://alpine:3.12
  args [
    "./scripts/validate_output.py",
    "./data/global_per_capita_mean.csv"
  ]
```

The above runs every script within a Docker container. As you would 
expect, this workflow fails to run since the `alpine:3/12` image is a 
lightweight one (contains only Bash utilities), and the dependencies 
that the scripts need are not be available in this image. In cases 
like this, we need to either [use an existing docker image][search] 
that has all the dependencies we need, or [create a docker image 
ourselves][create].

In this particular example, these scripts depend on CURL and Python. 
Thankfully, docker images for these already exist, so we can make use 
of them as follows:

```hcl
- uses: docker://byrnedo/alpine-curl:0.1.8
  args: ["scripts/download-data.sh"]

- uses: docker://python:3.7
  args: ["./scripts/get_mean_by_group.py", "5"]

- uses: docker://python:3.7
  args [
    "./scripts/validate_output.py",
    "./data/global_per_capita_mean.csv"
  ]
```

The above workflow runs correctly anywhere where Docker containers can 
run.

[search]: https://hub.docker.com
[create]: https://docs.docker.com/get-started/part2/
