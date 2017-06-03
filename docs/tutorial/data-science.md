# Example: Data Science

The following describes a series of steps to 
bootstrap a data science paper that follows the Popper convention 
using the Popper-CLI tool. Popper in this scenario is followed so that 
datasets are properly referenced and analysis scripts used to process 
data (as well as any output data) are versioned and associated to an
article. For more on the Popper convention, look at the [[Intro to Popper]] article.

While in this guide we use LATeX, Docker, dpm and Jupyter, any of 
these can be swapped for equivalent tools. To learn more about how to 
use other tools and how the Popper convention is toolchain-agnostic, 
see [here](https://github.com/systemslab/popper/wiki/Intro-to-Popper#popper-compliant-tools).

Requirements:

  * [git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)
  * [docker](https://docs.docker.com/engine/installation/)
  * [popper-cli](https://github.com/systemslab/popper/releases)

**Initialize a Popper Repository**

Our Popper-CLI tool assumes a git repository exists. To create one:

```bash
mkdir mypaper
cd mypaper
git init
echo "# My Paper Repo" > README.md
git commit -m "First commit of my paper repo."
```

See 
[here](https://help.github.com/articles/good-resources-for-learning-git-and-github/) 
for a list of good resources for learning git. Once a git repo exists, 
we can invoke the popper-cli tool:

```bash
cd mypaper
popper init
```

The above creates a `.popper.yml` file that contains configuration 
options for the CLI tool. This file should be committed to the paper 
repository (git repo we create above). For an explanation on the 
folder structure of a Popper repo, see [here](getting-started).

**Adding a New Experiment**

The Popper convention outlines how to make it practical to generate 
reproducible experiments. As part of our effort, we maintain a list 
of experiment templates that have been "popperized" (see 
[here](https://github.com/systemslab/popper/wiki/Intro-to-Popper#popper-compliant-experiments) for an 
explanation of what constitutes a Popper-compliant experiment). To see 
a list of available experiments:

```bash
popper experiment list
```

In order to add a new experiment, we refer to a template and assign a 
name to it. The general invocation form is the following:


```bash
popper experiment add <template> <experiment-name>
```

For example, assume we want to analyze data from an experiment in the 
area of meteorological sciences (a template created as part of the 
[Big Weather Web project](http://bigweatherweb.org)):

```bash
popper experiment jupyter-bww myexperiment
```

This data analysis experiment consists of one dataset and a jupyter 
notebook. To retrieve the dataset to the local machine:


```bash
cd experiments/myexperiment

docker run --rm -v `pwd`/datapackages:/datapackages \
  ivotron/dpm install /datapackages/air-temperature
```

> **NOTE**: The above makes use of the 
> [`dpm`](https://github.com/frictionlessdata/dpm) tool for managing 
[`datapackages`](http://frictionlessdata.io/about/). The tool doesn't 
support `file:///` URLs yet (until this 
[issue](https://github.com/frictionlessdata/dpm/issues/55) gets 
resolved). In the meantime, to download the dataset from github, 
replace `/datapackages/air-temperature`  with 
`https://github.com/ivotron/air-temperature`.


To visualize and interact with the data analysis of this experiment:

```bash
cd experimetns/myexperiment
./visualize
```

The above opens a browser and points it to the notebook. In this
example, the dataset used by the notebook resides in the 
`myexperiment/datapackages/` folder.

For this experiment we assume that input data has been externally 
generated, i.e. dataset creation is not part of the experiment. Also, 
the analysis runs on a single machine. Other types of data science 
projects might involve generating their input datasets and/or process 
data in a cluster of machines. Popper still can be followed in these 
scenarios (e.g. see [[Popper-Distributed-Systems]] and 
[[Popper-HPC]]).

**Adding More Datasets**

Datasets are stored (or referenced) in the `datapackages/` (or 
`datasets/`) folder of each experiment, with one subfolder for each 
dataset. For examples datasets see 
[here](https://github.com/datasets). To add or reference a new 
dataset, one has to either provide a URL of the dataset, or inspect a 
the list of datapackages available in a data repository using the 
`dpm` tool. Available repositories are `github`, `ckan` and `thredds`.

> **NOTE**: Support for [THREDDS]() is not part of the official `dpm` 
> client yet. Work is being done in this as part of the [big weather 
> web project](http://bigweatherweb.org).

Once a dataset URL is available, one can install a package by doing

```bash
docker run --rm -v `pwd`/datapackages:/datapackages \
  ivotron/dpm install http://motherlode.ucar.edu:8080/thredds/bww/
```

To display the info for a package, use the `info` command of `dpm`. 
For more info on how to use `dpm` take a look at the official 
[documentation](https://github.com/frictionlessdata/dpm).

**Generating Image Files For Reference In Manuscripts**

Assume we add a new type of analysis to the notebook and we want to 
generate an image. For the notebook of our example 
([`xarray-tutorial.ipynb`](https://github.com/Unidata/unidata-users-workshop/blob/master/notebooks/xray-tutorial.ipynb) 
of the `jupyter-bww` experiment), we can generate a file for figure 2 
(Line `[45]`). In Jupyter, we add a new cell below the figure and type 
the following line:

```python
plt.savefig('air-temperature.png',bbox_inches='tight', dpi=300)
```

Since the experiment folder is available in the filesystem that 
Jupyter has available to it, the figure persists even after the 
Jupyter server exits. To automatically re-execute the analysis and 
re-generate figures from a notebook, one can use the `run-notebook` 
script contained in the `jupyter-bww` experiment:

```bash
cd myexperiment
./run-notebook
```

**Documenting the Experiment**

After we're done with our experiment, we might want to document it and 
add a paper. We can use the generic `article` latex template or other 
more domain-specific one (available 
[here](https://github.com/systemslab/popper)). To display the 
available templates we do `popper paper list`. In this example we'll 
use the latex template for articles that appear in the [Bulletin of 
the American meteorological Society 
(BAMS)](http://journals.ametsoc.org/loi/bams):

```bash
popper paper add latex-ametsoc
```

Let's assume we will have a new section in the LATeX file where we 
describe our experiment. We will make use of the figure that we 
generated in the previous section. We can make the assumption that the 
experiments folder is available at the level of the latex file, so we 
can reference the image directly. For example:

```tex
\begin{figure}[t]
  \includegraphics{experiments/myexperiment/air-temperature.png}\\
  \caption{Air temperature.}\label{f1}
\end{figure}
```

And to re-generate the PDF containing the new image:

```bash
cd paper
./build
```

**Documenting Changes to Experiments**

The paper repository is the analogy to the lab notebook in 
experimental science. There are many ways in which these changes can 
be registered in the form of code repository commits. A couple of 
tips:

  * Make changes small. Avoid having large commits since that makes it 
    harder to document.
  * Separate commits that change the logic of the experiment and 
    analysis, from the ones that record changes to results.
  * Commit messages should describe in as much detail as possible the 
    changes to the experiment, or the new results being added to the 
    repository.

For examples of Popperized repositories, see [here](Popper-Examples). 
We are currently working with researchers in this domain to include 
more experiments to our [templates 
repository](https://github.com/systemslab/popper). If you are 
interested in contributing one but are not certain on how to start, 
please feel free to [email us](ivo@cs.ucsc.edu), 
[chat](https://gitter.im/systemslab/popper) or [open an 
issue](https://github.com/systemslab/popper/issues/new).
