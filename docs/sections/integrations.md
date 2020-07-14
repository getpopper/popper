# Exporting Workflows

This section describes how to convert a Popper workflow to other 
formats in order to execute on other services or scheduling 
frameworks.

## Airflow

Assuming we have a workflow in our repository whose structure looks 
like the following:

```
myrepo/
  workflows/
    wf.yml
  scripts/
    do_stuff.sh
```

And the workflow looks like:

```yaml
steps:
- id: first
  uses: docker://alpine:3.12
  args: [-c, "echo 'this will be read by the next steps' > output.txt]

- id: second
  uses: docker://alpine:3.12
  args: [-c, scripts/do_stuff.sh]
````

And we invoke this locally by running:

```bash
cd myrepo/

popper run -f workflows/wf.yml
```

Note that in the above, the workspace is `myrepo/`, hence the workflow 
references paths with respect to the root of the repository.

-----

Now, suppose we want to periodically run this workflow in Airflow. In 
order to do so we can create an airflow DAG out of this workflow:

```bash
cd myrepo/

popper export -f workflows/wf.yml -t airflow -o workflows/wf_dag.py

.airflow.py
```

And the generated DAG file looks something like:

```python
# TODO
```

We can then tweak the generated `workflows/wf_dag.py` DAG file to our 
needs by selecting how often to run it, whether to email on failure, 
etc. (see [here for more on which arguments are available]()).

After we're done configuring the workflow parameters for this 
workflow, we can commit this DAG file into our repository and push to 
a remote. So our repository now looks like:

```
myrepo/
  workflows/
    wf.yml
    wf_dag.py
  scripts/
    do_stuff.sh
```

Then, on the Airflow instance where this will be periodically running, 
we can clone our repository into the `$AIRFLOW_HOME/dags` folder. This 
would result in the following:

```
$AIRFLOW_HOME/
  airflow.db
  airflow.cfg
  dags/
    myrepo/
      workflows/
        wf.yml
        wf_dag.py
      scripts/
        do_stuff.sh
```

After having the above, Airflow should show the new dag when doing:

```bash
airflow list_dags
```

or by looking at the list of new dags in the Airflow web UI. Read the 
official [Airflow documentation]() for more details on how to make use 
the web UI, strategies for managing and synchronizing the DAG folder 
with hooks, among many other things.
