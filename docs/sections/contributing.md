# Contributing

## Code of Conduct

Anyone is welcome to contribute to Popper! To get started, take a look 
at our [contributing guidelines](CONTRIBUTING.md), then dive in with 
our [list of good first 
issues](https://github.com/systemslab/popper/issues?utf8=%E2%9C%93&q=is%3Aissue+label%3A%22good+first+issue%22+is%3Aopen) 
and [open projects](https://github.com/systemslab/popper/projects).

Popper adheres to the code of conduct [posted in this 
repository](CODE_OF_CONDUCT.md). By participating or contributing to 
Popper, you're expected to uphold this code. If you encounter 
unacceptable behavior, please immediately [email 
us](mailto:ivo@cs.ucsc.edu).

## Contributing CLI features

To contribute new CLI features:

 1. Add a [new issue][ghnew] describing the feature.
 2. Fork the [official repo][poppergh] and implement the issue on a 
    new branch.
 3. Add tests for the new feature. We test the `popper` CLI command 
    using Popper itself. The Popper pipeline for testing the `popper` 
    command is available 
    [here](https://github.com/systemslab/popper/blob/master/ci/).
 4. Open a pull request against the `master` branch.

## Contributing example pipelines

We invite anyone to implement (and document) Popper pipelines 
demonstrating the use of a DevOps tool, or how to apply Popper in a 
particular domain. Implementing a new example is done in two parts.

### Implement the pipeline

A popper pipeline is implemented by following the convention. See the 
[Concepts](concepts.html) and [Examples](examples.html) section for 
more.

Once a pipeline has been implemented, it needs to be uploaded to 
github, gitlab or any other repo publicly available. We use the 
organization <https://github.com/popperized> to host examples 
developed by the Popper team and collaborators. Pipelines on this 
organization are available by default to the [`popper 
search`](cli_features.html#searching-and-importing-existing-pipelines) 
command, so users can add it easily to their repos (using `popper 
add`). To add a repository containing one or more pipelines to this 
organization, please first create the repository on GitHub under an 
organization you own, and then either transfer ownership of the repo 
to the `popperized` organization, or [open an issue][ghnew] requesting 
the repository to be forked or mirrored (**NOTE**: forks and mirrors 
are need to be updated manually in order to reflect changes done on 
the base/upstream repository).

### Document the pipeline

We encourage contributors to document pipelines by adding them to our 
[list of examples](examples.html) of the official documentation. To 
add new documentation:

 1. Fork the [official repo][poppergh].
 2. Add a new section on the 
    [`docs/sections/examples.md`](https://github.com/systemslab/popper/blob/master/docs/sections/examples.md) 
    file.
 3. Open pull request against the `master` branch.

[ghnew]: https://github.com/systemslab/popper/issues/new
[poppergh]: https://github.com/systemslab/popper
