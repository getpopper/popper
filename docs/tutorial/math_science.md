## Example: Math Sciences

We describe how to bootstrap a scientific exploration that follows 
Popper in the mathematical sciences domain. For a generic description 
of how to follow Popper, see [here](Popper-From-Scratch). A typical 
exploration in this domain consists of code that implements some 
numerical computation and, possibly, input datasets used for the 
experiment. In this case, Popper is followed to manage the changes 
done to the scripts used to compile, install and run the experiment, 
as well as analyze its results.

Dependencies:

  * [Git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)
  * [Docker](https://docs.docker.com/engine/installation/)


We have several experiments available via the Popper-CLI tool 
(obtained from the [templates 
repository](https://github.com/systemslab/popper)). Assuming the repo 
has been initialized (see 
[here](Popper-Data-Science#initialize-a-popper-repository) for how 
to), we can show the list of available experiments by doing:

```bash
$ cd $HOME/mypaper
$ popper experiment list
```

In this example we'll make use of the 
[`blis`](https://github.com/systemslab/popper/tree/master/experiments/blis) 
experiment:

```bash
$ popper experiment add blis blis-vs-others

$ ls experiments/blis-vs-others
total 16K
-rwxr-x--- 1 ivo ivo  157 Oct  5 10:35 analyze.sh
drwxrwx--- 2 ivo ivo 4.0K Oct  5 10:35 results/
-rwxr-x--- 1 ivo ivo  325 Oct  5 10:35 run.sh
```

[BLIS](https://github.com/flame/blis) is a portable software framework 
for instantiating high-performance BLAS-like dense linear algebra 
libraries. This experiment corresponds to the one presented in the 
[first BLIS paper](http://doi.acm.org/10.1145/2764454). A [subsequent 
report](http://dl.acm.org/citation.cfm?id=2738033) documents how to 
repeat this experiment. This Popper template corresponds to sections 
2.1-2.3 of the replicability report.

To avoid having users configure and recompile the code every time one 
intends to repeat the experiment, we created [a Docker 
image](https://github.com/ivotron/docker-blis/tree/master/Dockerfile) 
that has all the binaries for BLIS, OpenBLAS and Atlas precompiled. 
Modifying and rebuilding the image is also possible (see 
[here](https://docs.docker.com/engine/tutorials/dockerimages/) for 
documentation). The `run.sh` script pulls the Docker image and 
executes the experiment, generating output to the `results/` folder.

The output consists of Matlab files. The `results/` folder also 
contains a set of scripts for generating Figures 13-15 from the 
original paper. The `analyze.sh` script launches a 
[Jupyter](http://jupyter.org/) notebook server (using Docker) that 
executes this scripts and generates the graphs. To see an example of 
how the notebook looks see 
[here](https://github.com/systemslab/popper/blob/master/experiments/blis/results/visualize.ipynb).

We are currently working with researchers in this domain to include 
more experiments to our [templates 
repository](https://github.com/systemslab/popper). If you are 
interested in contributing one but are not certain on how to start, 
please feel free to [email us](ivo@cs.ucsc.edu), 
[chat](https://gitter.im/systemslab/popper) or [open an 
issue](https://github.com/systemslab/popper/issues/new).
