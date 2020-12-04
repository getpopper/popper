# Life of a Workflow

This section explains what popper does when it executes a workflow. We will break down what popper does behind the scenes when executing the sample workflow described [here](https://github.com/getpopper/popper/blob/master/docs/sections/getting_started.md).

Each step of a workflow has the following stages:

## 1. Look at `uses` attribute and pull/build image

Each step of a workflow must specify the `DockerFile` or Docker image it will use to create a container with a `uses` line. For example, the first step of our example workflow contains the following line:
```
uses: docker://byrnedo/alpine-curl:0.1.8
```
These statements may refer to a `Dockerfile` inside the same repository as the workflow; a `Dockerfile` inside an external, public repository or container registry; or an image in a registry.

The example `uses` line above would result in the following output from Popper:
```
[download] docker pull byrnedo/alpine-curl:0.1.8
```
This line indicates that the necessary image was successfully pulled by docker. If the image needs to be built from a Dockerfile, it will do so at this stage. 

The workings and limitations of `uses` and other possible attributes for a workflow are outlined [here](cn_workflows.md).

## 2. Configure and create container

Popper instantiates containers in the underlying engine (with Docker as the default) using basic configurations options. The underlying engine configuration can be modified using a configuration file. Learn more about configuring the engine [here](cn_workflows.md).

In the example workflow, the first step contains the following lines, one for the `id` (which is used as the name of the step) and one for the `args`:

```
id: download
```
```
args: [-LO, https://github.com/datasets/co2-fossil-global/raw/master/global.csv]
```
Using these inputs, Popper executes the following command:
```
[download] docker create name=popper_download_f20ab8c9 image=byrnedo/alpine-curl:0.1.8 command=['-LO', 'https://github.com/datasets/co2-fossil-global/raw/master/global.csv']
```
This creates a docker container from the image given by the `uses` line with inputs from the `args` line, and with a name created using the id given in the `id` line and the id number of our specific workflow.

## 3. Launch container

Popper launches the container, waits for it to be done, and then prints the resulting output.

In the example workflow, the first step produces the following output:
```
[download] docker start
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100   144    0   144    0     0    500      0 --:--:-- --:--:-- --:--:--   500
100  6453  100  6453    0     0  10509      0 --:--:-- --:--:-- --:--:-- 25709
Step 'download' ran successfully !
```

## 4. Move on to next step

The above three stages comprise a single step in a workflow's execution. As workflows can be made up of multiple steps, the workflow continues its execution by progressing to its next step, which contains its own `uses` and configurations for its containers and operations. Thus, your average workflow looks something like this:

```
steps:
- id: <optional step name>
  uses: <some local/public repository or container registry>
  args: [<command>, ..., <command>]

- id: <Optional step name>
  uses: <some local/public repository or container registry>
  args: [<command>, ..., <command>]
  .
  .
  .
```

The workflow repeats the same three stages for each step in the process. Consequently, the next step of our example workflow produces the following output:
```
[get-transpose] docker pull getpopper/csvtool:2.4
[get-transpose] docker create name=popper_get-transpose_f20ab8c9 image=getpopper/csvtool:2.4 command=['transpose', 'global.csv', '-o', 'global_transposed.csv']
[get-transpose] docker start
Step 'get-transpose' ran successfully !
Workflow finished successfully.
```

Once the workflow has executed all of its outlined steps, its lifecycle is complete!

## Conclusion

Hopefully this section has clarified how a Popper workflow iterates through its steps to simplify any workflow into a simple `popper run` call. Even our simple example workflow would have required the following commands be typed manually:

1. Downloading the needed image of Alpine Curl
```
docker pull byrnedo/alpine-curl:0.1.8
```
2. Building the downloaded Alpine Curl image
```
docker create name=popper_download_f20ab8c9 image=byrnedo/alpine-curl:0.1.8 command=['-LO', 'https://github.com/datasets/co2-fossil-global/raw/master/global.csv']
```
3. Downloading the dataset from the repository
```
docker start
```
4. Downloading the needed image of csvtools
```
docker pull getpopper/csvtool:2.4
```
5. Building the downloaded image of csvtools
```
docker create name=popper_get-transpose_f20ab8c9 image=getpopper/csvtool:2.4 command=['transpose', 'global.csv', '-o', 'global_transposed.csv']
```
6. Performing the command to transpose the earlier downloaded dataset
```
docker start
```

Thus, Popper can be a useful tool for increasing efficiency on any workflow-heavy project!
