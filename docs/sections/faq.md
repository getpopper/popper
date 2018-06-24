# FAQ

### How can we deal with large datasets? For example I have to work on large data of hundreds GB, how would this be integrated into Popper?

For datasets that are large enough that they cannot be managed by Git, 
solutions such as a PFS, GitLFS, Datapackages, ckan, among others 
exist. These tools and services allow users to manage large datasets 
and version-control them. From the point of view of Popper, this is 
just another tool that will get invoked as part of the execution of a 
pipeline. As part of our documentation, we have examples on how to use 
datapackages, and another on how to use data.world.

### How can Popper capture more complex workflows? For example, automatically restarting failed tasks?

A Popper pipeline is a simple sequence of bash scripts. Popper is not 
a replacement for scientific workflow engines, instead, its goal is to 
capture the highest-most workflow: the human interaction with a 
terminal. For more on this, please take a look at the [Popper vs. 
other 
software](http://popper.rtfd.io/en/docs-reorg/sections/concepts.html#scientific-workflow-engines) 
section of our documentation.

### Can I follow Popper in computational science research, as opposed to computer science?

Yes, the goal for Popper is to make it a domain-agnostic 
experimentation protocol. Examples of how to follow Popper on distinct 
domains: [atmospheric science](), [computational neuroscience](), 
[genomics]() and [applied math]().


### How to apply the Popper protocol for applications that take large quantities of computer time?

The `popper run` command has a `--skip` argument that can be used to 
execute a pipeline in multiple steps. So for example, assuming we have 
a pipeline with the following scripts: `setup`, `run`, `post-run` and 
`validate`, then, you could run:

```bash
popper run --skip post-run,validate
```

which would run the first part (setup and execution). Then, later you 
either manually check whether your jobs are done or you automate it in 
the `post-run` script (I know SLURM has a way of querying the status 
of your jobs) and run:

```bash
popper run --skip setup.sh,run.sh
```

and the above will just execute the second half of your pipeline. The 
`post-run` script could either first check the status of your jobs, or 
just assume that they’re done and will `scp` the data to your local 
machine (or move output to a NAS, etc.), and the `validate` will 
invoke the analysis.

-----

Another practice we have been following is to have a specific set of 
parameters for the pipeline with the goal of running a smaller scale 
simulation/analysis. The idea is to use this when running on a CI 
service such as [Travis](https://travis-ci.org) in order to test the 
entire pipeline in a relatively short amount of time (Travis times out 
jobs after 3 hours). So this ends up looking something like 
[this](https://github.com/ivotron/quiho-popper/blob/master/pipelines/single-node/setup.sh), 
i.e. a conditional in a stage that, depending on the environment (in 
this case a `CI` variable defined), the parametrization and setup is 
different, but the rest of the pipeline runs in the same fashion. 
While this approach doesn't really executes the actual original 
simulation, at least it lets us test the integrity of the scripts.
