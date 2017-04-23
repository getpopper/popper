# Popper for HPC papers

We describe how to use Popper in high performance computing (HPC) 
scenarios. A typical experiment in HPC assumes many things from the 
environment: an NFS mount point available in compute nodes, a batch 
scheduler, applications installed/compiled directly on the host (i.e. 
without any type of virtualization), among others. In this case, 
Popper is followed to record the scripts used to compile, install and 
run the experiment, as well as analyze its results.

Dependencies:
  * [Git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)
  * [Spack](https://github.com/llnl/spack/)
  * [Docker](https://docs.docker.com/engine/installation/)

We assume that the `$HOME/mypaper` folder is available in the users' 
laptop as well as on the nodes of the machine where the experiment 
runs.

# Adding the experiment

We have several experiments available via the Popper-CLI tool 
(obtained from the [templates 
repository](https://github.com/systemslab/popper)). Assuming the repo 
has been initialized (see [here 
this](Popper-Data-Science#initialize-a-popper-repository)), we can 
show the list of available experiments by doing:

```bash
$ cd $HOME/mypaper
$ popper experiment list
```

In this example we'll make use of the 
[`mpip`](https://github.com/systemslab/popper/tree/master/templates/experiments/mpip) 
experiment:

```bash
$ popper experiment add mpip mpip-lulesh

$ ls experiments/mpip-lulesh
total 16K
-rwxr-x--- 1 ivo ivo  157 Oct  5 10:35 analyze.sh
-rwxr-x--- 1 ivo ivo  253 Oct  5 10:35 install.sh
drwxrwx--- 2 ivo ivo 4.0K Oct  5 10:35 results/
-rwxr-x--- 1 ivo ivo  325 Oct  5 10:35 run.sh
```

The experiment corresponds to an execution of the 
[LULESH](https://codesign.llnl.gov/lulesh.php) MPI [proxy 
application](http://www.lanl.gov/projects/codesign/proxy-apps/assets/docs/proxyapps_strategy.pdf)
compiled against [mpiP](http://mpip.sourceforge.net/). The experiment 
consists of three scripts: `install.sh` installs the dependencies via 
[`spack`](https://github.com/llnl/spack/); `run.sh` executes LULESH; 
and `analyze.sh` post-process the results that are gathered by `mpiP`.

Since `spack` installs dependencies from source, the `install.sh` 
script should be executed in a node with the same architecture as the 
one of the compute nodes where LULESH will run (e.g. in a "head" node 
of the machine). The `run.sh` script is passed to the batch scheduler, 
which is SLURM in this case. Once the experiment finishes, `mpiP` 
places a text file in the `results/` folder (a text file file ending 
in `.mpiP`) that contains MPI runtime metrics. The `analyze.sh` script 
launches a [Jupyter](http://jupyter.org/) notebook server (using 
Docker) that analyzes the output of `mpiP` and generates a graph 
summarizing MPI statistics. To see an example of how the notebook 
looks see 
[here](https://github.com/systemslab/popper/blob/master/templates/experiments/mpip/results/notebook.ipynb).

We are currently working with researchers in this domain to include 
more experiments to our [templates 
repository](https://github.com/systemslab/popper). If you are 
interested in contributing one but are not certain on how to start, 
please feel free to [email us](ivo@cs.ucsc.edu), 
[chat](https://gitter.im/systemslab/popper) or [open an 
issue](https://github.com/systemslab/popper/issues/new).
