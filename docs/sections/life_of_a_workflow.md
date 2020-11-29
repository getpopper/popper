# Life of a Workflow

This section explains what popper does when it executes a workflow.

List the 4 steps that Popper uses to execute a workflow For each of
these steps, we provide an example of how it was executed. We use
https://github.com/getpopper/popper/blob/master/docs/sections/getting_started.md
as the example

Popper follows four steps to execute a workflow. For each of the steps, 

Popper executes a workflow using the following steps.

## Look at `uses` attribute and pull/build image



```
[download] docker pull byrnedo/alpine-curl:0.1.8
```

## Configure and create container

## Launch container, wait for it to be done

## Move on to next step

<comment>

At the end, add note emphasizes how workflows codify a task that would
be otherwise manually done.  Explain what a person would do in a
terminal in order to run the example workflow. list the actual
commands that would be manually typed in a terminal, one for each of
the tasks that Popper automates.

</comment>


<ol>
  <li>Look at `uses` attribute and pull/build image</li>
  Explanation
  Ex. [download] docker pull byrnedo/alpine-curl:0.1.8
  <li>Configure and create container</li>
  Explanation
  Ex.[download] docker create name=popper_download_f20ab8c9 image=byrnedo/alpine-curl:0.1.8 command=['-LO', 'https://github.com/datasets/co2-fossil-global/raw/master/global.csv']
  <li>Launch container, wait for it to be done</li>
  <li>Move on to next step</li>
</ol>
