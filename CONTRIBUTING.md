# Contributing to Popper

Thank you for your interest in contributing to Popper :tada:!

This document is a part of a set of guidelines for contributing to Popper on 
GitHub. These are guidelines, not rules. This guide is meant to make it easy for 
you to get involved.

Our goal is to make it easier for programmers to use DevOps tools and follow 
software engineering best-practices when they implement experimentation 
pipelines. Our goal is to lower the barriers for collaboration and the sharing 
of knowledge.

## Participation guidelines

Popper adheres to our code of conduct, [posted in this repository](CODE_OF_CONDUCT.md). By participating or contributing to Popper, you're expected to uphold this code. If you encounter unacceptable behavior, please immediately [email us](mailto:ivo@cs.ucsc.edu).

## What to work on

Take a look at the issues in our [list of 
projects](https://github.com/systemslab/popper/projects) to get started!

### Keywords in Issue Titles

The title of each open issue is prefixed with a keyword that denotes the 
following:

  * `cli`. An issue that involves modifying code of the 
    [`CLI`](https://github.com/systemslab/popper/tree/master/cli) tool.

  * `doc`. An issue that involves modifying the 
    [documentation](https://github.com/systemslab/popper/tree/master/docs).

  * `actions`. An issue that involves the creation, modification or maintenance 
    of an action. This might be hosted in an external repo, such as the repos 
    that are pare of the [`popperized`](https://github.com/popperized) 
    organization.

  * `example`. An issue that involves the creation of an example 
    Workflow that showcases available features of the CLI tool, as 
    well as the catalog of pre-defined actions.

### Branches

There are two main branches of the codebase:

  * [`v1.x`](https://github.com/systemslab/popper/tree/v1.x). This branch tracks 
    the older version of the CLI tool which supported workflows being defined in 
    YAML format. This is documented 
    [here](https://popper.readthedocs.io/en/v1.1.2/sections/cli_features.html#the-popper-yml-configuration-file).
  * [`master`](./). This tracks the latest 2.x series, which adopted 
    Github actions workflows as the main supported format.

### Install Popper from Source

To install Popper in "development mode", we suggest the following 
approach:

```bash
cd $HOME/

# create virtualenv
virtualenv $HOME/venvs/popper
source $HOME/venvs/popper/bin/activate

# clone popper
git clone git@github.com:systemslab/popper
cd popper

# install popper from source
pip install -e cli/
```

the `-e` flag passed to `pip` tells it to install the package from the 
source folder, and if you modify the logic in the popper source code 
you will see the effects when you invoke the `popper` command. So with 
the above approach you have both (1) popper installed in your machine 
and (2) an environment where you can modify popper and test the 
results of such modifications.

## How to contribute changes

Once you've identified one of the issues above that you want to contribute to, you're ready to make a change to the project repository!

 1. **[Fork](https://help.github.com/articles/fork-a-repo/) this repository**. 
    This makes your own version of this project you can edit and use.
 2. **[Make your 
    changes](https://guides.github.com/activities/forking/#making-changes)**! 
    You can do this in the GitHub interface on your own local machine. Once 
    you're happy with your changes...
 3. **Submit a [pull 
    request](https://help.github.com/articles/proposing-changes-to-a-project-with-pull-requests/)**. 
    This opens a discussion around your project and lets the project lead know 
    you are proposing changes.

First time contributing to an open source project? Check out this guide on [how to contribute to an open source project on GitHub](https://egghead.io/series/how-to-contribute-to-an-open-source-project-on-github).

## How to report bugs

We track bugs as [GitHub issues](https://github.com/systemslab/popper/issues). Before posting a bug as a new issue, [please do a search](https://github.com/systemslab/popper/issues?q=is%3Aopen+is%3Aissue+label%3Abug) to see if the bug you're experiencing was already reported by someone else. If it was, add a comment to that issue instead of creating a new one.

### How to submit good bug reports

A more detailed bug report will help people track down and fix your issue faster. Try to include the following in your bug report if you can: 

* Create a detailed title in your report to properly explain your issue
* Include any screen captures or terminal output if necessary.
* List what version of Popper you are using.
* Describe an exact sequence of steps that can reproduce your issue. If you can't reliably replicate your issues, explain what you were doing before the problem happened and how often it happens.
* Is this a new bug? Include when you started having these issues.

Post any bugs, requests, or questions on the [GitHub issues page for Popper](https://github.com/systemslab/popper/issues)!

## Communication channels

If want to contribute and you're still not certain on how to start please feel
free to [email us](mailto:ivo@cs.ucsc.edu),
[chat on Gitter](https://gitter.im/systemslab/popper) or [open an
issue](https://github.com/systemslab/popper/issues/new).
