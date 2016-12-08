# Single-node WRF numeric reproducibility

Runs WRF and checks output to determine whether there are numeric 
differences between distinct executions.

To execute the experiment:

 1. Edit the `ansible/machines` file to specify the hostnames of 
    machines where the WRF containers will run. The default is 
    `localhost`, so if you are running on you want to execute on your 
    local machine, then you can skip this step.
 2. If applicable, modify WRF parameters in `vars.yml`.
 3. Invoke `run.sh`

The `run.sh` script assumes that `id_rsa` or `id_dsa` are the SSH 
identity files used to authenticate with the remote hosts.

Validation (comparison of output) is executed by invoking the 
`validate.sh` script.
