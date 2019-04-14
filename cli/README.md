# Popper-CLI

A CLI tool to help bootstrap projects that follow the
[Popper](https://github.com/systemslab/popper) convention. For a
quickstart guide on how to use the CLI, look
[here](http://popper.readthedocs.io/en/latest/protocol/getting_started.html#quickstart-guide).

## Install

### `pip`

We have a [`pip`](https://pypi.python.org/pypi) package available. To
install:

```bash
pip install popper
```

## Usage

To get an overview and list of commands check out the command line
help:

```bash
popper --help
```

## Bash-completion
To enable auto-completion support, you will need to activate the bash-completion.sh script
inside the `cli/extras` folder. This can be done by copying this script to
`/etc/bash_completion.d/` or `/usr/local/etc/bash_completion.d/`. Before this, you need to
have bash-completion enabled/installed. Refer to [this guide](https://github.com/bobthecow/git-flow-completion/wiki/Install-Bash-git-completion)
for the instructions.

When done with the above,
go to the extras folder and copy and paste the following commands in your terminal :-

```bash
 cp ./bash-completion.sh /etc/bash_completion.d/popper.sh
```

or

```bash
cp ./bash-completion.sh /usr/local/etc/bash_completion.d/popper.sh
```
