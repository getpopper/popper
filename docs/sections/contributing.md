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

 1. Add a [new issue](https://github.com/systemslab/popper/issues/new) 
    describing the feature.
 2. Fork the repo and implement the issue on a new branch.
 3. Add tests for the new feature. We test the `popper` CLI command 
    using Popper itself. The pipeline is available 
    [here](https://github.com/systemslab/popper/blob/master/ci/).
 4. Open a pull request against the `master` branch.

## Contributing example pipelines

We invite anyone to implement (and document) Popper pipelines 
demonstrating the use of a DevOps tool, or how to apply Popper in a 
particular domain. Implementing a new example is done in two parts.

### Implement the pipeline

A popper pipeline is implemented by following the convention. See the 
[Concepts](concepts.md)

We use the organization <https://github.com/popperized> to host 
examples. Pipelines hosted on this organization are available by 
default to the `popper search` command, so users can add it easily to 
their repos (using `popper add`). Alternatively, 

### Document the pipeline


