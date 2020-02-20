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

## Install from source

To install Popper in "development mode", we suggest the following 
approach:

```bash
cd $HOME/

# create virtualenv
python -m virtualenv $HOME/virtualenvs/popper

# load virtualenv
source $HOME/virtualenvs/popper/bin/activate

# clone popper
git clone git@github.com:systemslab/popper
cd popper

# install popper from source
pip install -e cli
```

The `-e` flag passed to `pip` tells it to install the package from the 
source folder, and if you modify the logic in the popper source code 
you will see the effects when you invoke the `popper` command. So with 
the above approach you have both (1) popper installed in your machine 
and (2) an environment where you can modify popper and test the 
results of such modifications.

> **NOTE**: The virtual environment created above needs to be reloaded 
> every time you open a new terminal window (`source` commmand), 
> otherwise the `popper` command will not be found by your shell.

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

We invite anyone to implement and document Github Action workflows. To 
add an example, you can fork an open a PR on the 
<https://github.com/popperized/popper-examples> repository.

[ghnew]: https://github.com/systemslab/popper/issues/new
[poppergh]: https://github.com/systemslab/popper
