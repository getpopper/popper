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
terminal.

### Can I follow Popper in computational science research, as opposed to computer science?

Yes, the goal for Popper is to make it a domain-agnostic 
experimentation protocol. See the [examples section](examples.html) 
for more.

### How to apply the Popper protocol for applications that take large quantities of computer time?

The `popper run` takes an optional `action` argument that can be used 
to execute a workflow up to a certain step. See 
[here](cli_features.html).
