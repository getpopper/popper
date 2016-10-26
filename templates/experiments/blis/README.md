# BLIS vs. other BLAS implementations

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
[here](https://github.com/systemslab/popper-templates/blob/master/experiments/blis/results/visualize.ipynb).
