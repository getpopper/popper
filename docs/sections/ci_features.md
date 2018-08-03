# CI features

## Environments


## List of executions


## How matrix execution works 

Popper supports a matrix syntax when using environment variables and execution environments.

This means that Popper will execute all possible combinations between those elements returning
a popper_status for each one of them.

Below is an example configuration for a build matrix that expands to 9 individual jobs

`.popper.yml`
```
envs:
    - host
    - alpine-3.4
    - debian-9
vars:
    - key1: val1
      key2: val2
    - key3: val3
      key4: val4
    - key5: val5
      key6: val6
      key7: val7
```

The previous syntax was achieved by executing the following commands: 
```
popper env-vars yourpipe --add key1=val1 --add key2=val2
popper env-vars yourpipe --add key3=val3 --add key4=val4
popper env-vars yourpipe --add key5=val5 --add key6=val6 --add key7=val7


popper env yourpipe --add alpine-3.4
popper env yourpipe --add debian-9
```

