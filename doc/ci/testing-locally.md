The idea behind PopperCI is simple: by structuring a project in a 
commonly agreed way, experiment execution and validation can be 
automated without the need for manual intervention. The structured 
looks like the following:

```bash
paper-repo/experiments/myexp/
├── README.md
├── .popper.yml
├── run.sh
├── setup.sh
├── teardown.sh
└── validate.sh
```

The [PopperCLI](https://github.com/systemslab/popper/popper) tool 
includes a `check` subcommand that can be executed to test locally. 
This subcommand is the same that is executed by the PopperCI service, 
so the output of its invocation should be, in most cases, the same as 
the one obtained when PopperCI executes it. This helps in cases where 
one is testing locally. To execute test locally:

```bash
cd my/paper/repo
popper check myexperiment

Popper check started
Running stage setup.sh ....
Running stage run.sh ................
Running stage validate.sh .
Running stage teardown.sh ..
Popper check finished: SUCCESS
```

The status of the execution is stored in the `popper_status` file, 
while `stdout` and `stderr` output for each stage is written to the 
`popper_logs` folder.

```bash
tree popper_logs
popper_logs/
├── run.sh.out
├── run.sh.err
├── setup.sh.out
├── setup.sh.err
├── teardown.sh.out
├── teardown.sh.err
├── validate.sh.out
└── validate.sh.err
```
