# Getting Started

Before going through this guide, you need to have the Docker engine 
installed on your machine (see [installations instructions 
here](https://docs.docker.com/install/)). In addition, this guide 
assumes familiarity with Linux containers and the container-native 
paradigm to software development. You can read a high-level 
introduction to these concepts in [this page](./concepts.md), where 
you can also find references to external resources that explain them 
in depth.

## Installation

To install or upgrade Popper, run the following in your terminal:

```bash
curl -sSfL https://raw.githubusercontent.com/getpopper/popper/master/install.sh | sh
```

## Create Your First Workflow

Assume that as part of our work we want to carryout two tasks: 

 1. Download a dataset (CSV) that we know is available at 
    <https://github.com/datasets/co2-fossil-global/raw/master/global.csv>
 2. Modify the dataset, specifically we want to get [the 
    transpose](https://en.wikipedia.org/wiki/Transpose) of the this 
    CSV table.

For the first task we can use [`curl`](https://curl.haxx.se/), while 
for the second we can use 
[`csvtool`](https://github.com/Chris00/ocaml-csv).

When we work under the container-native paradigm, instead of going 
ahead and installing these on our computer, we first look for 
available images on a container registry, for example 
<https://hub.docker.com>, to see if the software we need is available.

In this case we find two images that do what we need and proceed to 
write this workflow in a `wf.yml` file using your favorite editor:

```yaml
steps:
# download CSV file with data on global CO2 emissions
- id: download
  uses: docker://byrnedo/alpine-curl:0.1.8
  args: [-LO, https://github.com/datasets/co2-fossil-global/raw/master/global.csv]

# obtain the transpose of the global CO2 emissions table
- id: get-transpose
  uses: docker://getpopper/csvtool:2.4
  args: [transpose, global.csv, -o, global_transposed.csv]
```

## Run your workflow

To execute the workflow you just created:

```bash
popper run -f wf.yml
```

Since this workflow consists of two steps, there were two 
corresponding containers that were executed by the underlying 
container engine, which is Docker in this case. We can verify this by 
asking Docker to show the list of existing containers:

```bash
docker ps -a
```

You should see the two containers from the example workflow being 
listed along with other containers. The name of the containers created 
by popper are prefixed with `popper_`. To obtain more detailed 
information of what the `popper run` command does, you can pass the 
`--help` flag to it:

```bash
popper run --help
```

> **TIP**: All popper subcommands allow you to pass `--help` flag to 
> it to get more information about what the command does.

## Debug your workflow

From time to time, we find ourselves with a step that does not quite 
do what we want it to. In these cases, we can open an interactive 
shell instead of having to update the YAML file and invoke `popper 
run` again. In those cases, the `popper sh` comes handy. For example, 
if we would like to explore what other things can be done inside the 
container for the second step:

```bash
popper sh -f wf.yml get-transpose
```

And the above opens a shell inside a container instantiated from the 
`docker.io/getpopper/csvtool:2.4` image. In this shell we can, for 
example, obtain information about what else can the `csvtool` do:

```bash
csvtool --help
```

Based on this exploration, we can see that we can pass a `-u TAB` flag 
to the `csvtool` in order to generate a tab-separated output file 
instead of a comma-separated one. Assuming this is what we wanted to 
achieve in our case, we then quit the container by running `exit`.

Back on our host machine context, that is, not running inside the 
container anymore, we can update the second step by editing the YAML 
file to look like the following:

```yaml
- id: get-transpose
  uses: docker://getpopper/csvtool:2.4
  args: [transpose, global.csv, -u, TAB, -o, global_transposed.csv]
```

And test that what we changed worked by running in non-interactive 
mode again:

```bash
popper run -f wf.yml get-transpose
```

## Next Steps

  * Learn more about all the [CLI features](./cli_features.md) that 
    Popper provides.

  * Take a look at the ["Workflow Language"](./cn_workflows.html#syntax) 
    for the details on what else can you specify as part of a Step's 
    attributes.

  * Read the ["Popper Execution 
    Runtime"](./cn_workflows.html#execution-runtime) section to learn 
    more about what other execution environments Popper supports, as 
    well as how to customize the behavior of the underlying execution.

  * Browse existing [workflow 
    examples](https://github.com/getpopper/popper-examples).

  * Take a [self-paced 
    tutorial](https://popperized.github.io/swc-lesson/) to learn how 
    to use other features of Popper.
