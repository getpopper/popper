# CI features

## Environments


## List of executions


## How matrix execution works 

`Popper` supports a matrix syntax when using environment variables and execution environments.
This means that Popper will execute all possible combinations between those elements returning
a popper_status and its corresponding `.err` and `.out`' files for each one of them.

To achieve this, you only need to add your environment variables and your execution environments
as follows and `Popper` will do it for you automatically. 

For example, if you were to add your first set of environment variables, you'd execute the following:

`popper env-vars your-popper-pipe --add key1=val1 --add key2=val2`

This will cause the following to be added to your `.popper.yml` file. 

```
vars:
- key1: val1
  key2: val2
```

So far, we only have one possible combinations so let's add more.
You can use the same command to add more sets of environment variables to your 
matrix execution.

`popper env-vars your-popper-pipeline --add key3=val3 --add key3=val3`

Which will result in the following:

```
vars:
- key1: val1
  key2: val2
- key3: val3
  key4: val4
```

This is how all the configuration of your pipeline should look like so far assuming you
just made it using `popper init your-popper-pipeline`:

```
pipelines:
  your-popper-pipeline:
    envs:
    - host
    path: pipelines/pipe
    requirements: {}
    stages:
    - setup
    - run
    - post-run
    - validate
    - teardown
    vars:
    - key1: val1
      key2: val2
    - key3: val3
      key4: val4
```

Please notice that Popper automatically uses host as your default execution environment.
Then, so far we have a matrix execution which consists in the combinations between host
and your sets of environment variables. Let's add Debian 9 as an execution environment with the
following command:

`popper env your-popper-pipeline --add debian-9`

###### NOTE: Docker is required in order to run your project on an execution environment different from host

Your `envs:` section should now look like this: 

```
envs:
- host
- debian-9
```

Now, you only need to execute `popper run your-popper-pipeline` and Popper will automatically 
execute all of those possible combinations, this is how it should looks like: 

```bash
$ tree pipelines/your-popper-pipeline/popper
pipelines/your-popper-pipeline/popper
├── debian-9
│   ├── 0
│   │   ├── popper_status
│   │   ├── post-run.sh.err
│   │   ├── post-run.sh.out
│   │   ├── run.sh.err
│   │   ├── run.sh.out
│   │   ├── setup.sh.err
│   │   ├── setup.sh.out
│   │   ├── teardown.sh.err
│   │   ├── teardown.sh.out
│   │   ├── validate.sh.err
│   │   └── validate.sh.out
│   └── 1
│       ├── popper_status
│       ├── post-run.sh.err
│       ├── post-run.sh.out
│       ├── run.sh.err
│       ├── run.sh.out
│       ├── setup.sh.err
│       ├── setup.sh.out
│       ├── teardown.sh.err
│       ├── teardown.sh.out
│       ├── validate.sh.err
│       └── validate.sh.out
└── host
    ├── 0
    │   ├── popper_status
    │   ├── post-run.sh.err
    │   ├── post-run.sh.out
    │   ├── run.sh.err
    │   ├── run.sh.out
    │   ├── setup.sh.err
    │   ├── setup.sh.out
    │   ├── teardown.sh.err
    │   ├── teardown.sh.out
    │   ├── validate.sh.err
    │   └── validate.sh.out
    └── 1
        ├── popper_status
        ├── post-run.sh.err
        ├── post-run.sh.out
        ├── run.sh.err
        ├── run.sh.out
        ├── setup.sh.err
        ├── setup.sh.out
        ├── teardown.sh.err
        ├── teardown.sh.out
        ├── validate.sh.err
        └── validate.sh.out

```

You can see that Popper made a folder for each execution enviroment `host` and `debian-9` and
inside of each folder it made two folders `0` and `1` which represent the pair of sets of 
environment variables that we used, in other words

`0` means the first set: 
```
- key1: val1
  key2: val2
```

and `1` is the second set:
```
- key3: val3
  key4: val4
```

There you can find the status of the execution in `popper_status` as well as the output and errors
of each one of your stages.