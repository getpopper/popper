# Guides

This is a list of guides related to several aspects of working with 
Popper workflows.

## Choosing a location for your step

If you are developing a docker image for other people to use, we 
recommend keeping this image in its own repository instead of bundling
it with your repository-specific logic. This allows you to version, 
track, and release this image just like any other software. Storing a 
docker image in its own repository makes it easier for others to 
discover, narrows the scope of the code base for developers fixing 
issues and extending the image, and decouples the image's versioning 
from the versioning of other application code.

## Using shell scripts to define step logic

Shell scripts are a great way to write the code in steps. If you can 
write a step in under 100 lines of code and it doesn't require complex 
or multi-line command arguments, a shell script is a great tool for 
the job. When defining steps using a shell script, follow these 
guidelines:

-   Use a POSIX-standard shell when possible. Use the `#!/bin/sh`
    [shebang](https://en.wikipedia.org/wiki/Shebang_(Unix)) to use the
    system\'s default shell. By default, Ubuntu and Debian use the
    [dash](https://wiki.ubuntu.com/DashAsBinSh) shell, and Alpine uses
    the [ash](https://en.wikipedia.org/wiki/Almquist_shell) shell. Using
    the default shell requires you to avoid using bash or shell-specific
    features in your script.
-   Use `set -eu` in your shell script to avoid continuing when errors
    or undefined variables are present.


## Hello world step example

You can create a new step by adding a `Dockerfile` to the directory in 
your repository that contains your step code. This example creates a 
simple step that writes arguments to standard output (`stdout`). An 
step declared in a `main.workflow` would pass the arguments that this 
step writes to `stdout`. To learn more about the instructions used in 
the `Dockerfile`, check out the [official Docker 
documentation][howto-dockerfile]. The two files you need to create an 
step are shown below:

**./step/Dockerfile**

```Dockerfile
FROM debian:9.5-slim

ADD entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
```

**./step/entrypoint.sh**

```bash
#!/bin/sh -l

sh -c "echo $*"
```

Your code must be executable. Make sure the `entrypoint.sh` file has
`execute` permissions before using it in a workflow. You can modify the
permission from your terminal using this command:

```bash
chmod +x entrypoint.sh
```

This `echo`s the arguments you pass the step. For example, if you were 
to pass the arguments `"Hello World"`, you\'d see this output in the 
command shell:

```bash
Hello World
```

## Creating a Docker container

Check out the [official Docker documentation][howto-dockerfile].

[howto-dockerfile]: https://docs.docker.com/engine/reference/builder/

## Implementing a workflow for an existing set of scripts

This guide exemplifies how to define a Popper workflow for an existing 
set of scripts. Assume we have a project in a `myproject/` folder and 
a list of scripts within the `myproject/scripts/` folder, as shown 
below:

```bash
cd myproject/
ls -l scripts/

total 16
-rwxrwx---  1 user  staff   927B Jul 22 19:01 download-data.sh
-rwxrwx---  1 user  staff   827B Jul 22 19:01 get_mean_by_group.py
-rwxrwx---  1 user  staff   415B Jul 22 19:01 validate_output.py
```

A straight-forward workflow for wrapping the above is the following:

```yaml
- uses: docker://alpine:3.12
  runs: "/bin/bash"
  args: ["scripts/download-data.sh"]

- uses: docker://alpine:3.12
  args: ["./scripts/get_mean_by_group.py", "5"]

- uses: docker://alpine:3.12
  args [
    "./scripts/validate_output.py",
    "./data/global_per_capita_mean.csv"
  ]
```

The above runs every script within a Docker container. As you would 
expect, this workflow fails to run since the `alpine:3/12` image is a 
lightweight one (contains only Bash utilities), and the dependencies 
that the scripts need are not be available in this image. In cases 
like this, we need to either [use an existing docker image][search] 
that has all the dependencies we need, or [create a docker image 
ourselves][create].

In this particular example, these scripts depend on CURL and Python. 
Thankfully, docker images for these already exist, so we can make use 
of them as follows:

```yaml
- uses: docker://byrnedo/alpine-curl:0.1.8
  args: ["scripts/download-data.sh"]

- uses: docker://python:3.7
  args: ["./scripts/get_mean_by_group.py", "5"]

- uses: docker://python:3.7
  args: [
    "./scripts/validate_output.py",
    "./data/global_per_capita_mean.csv"
  ]
```

The above workflow runs correctly anywhere where Docker containers can 
run.

[search]: https://hub.docker.com
[create]: https://docs.docker.com/get-started/part2/

## Building images using BuildKit

[BuildKit](https://github.com/moby/buildkit) can be used as part of a workflow 
to build a container image:

```yaml
steps:
- id: build image using buildkit
  uses: docker://moby/buildkit:rootless
  runs: [buildctl-daemonless.sh]
  options:
    volumes:
    - $_DOCKER_CONFIG_DIR:/root/.docker/
  env:
    BUILDKITD_FLAGS: --oci-worker-no-process-sandbox
  args:
  - |
    build \
      --frontend dockerfile.v0 \
      --local context=/workspace/ \
      --local dockerfile=/workspace/my_container/Dockerfile \
      --import-cache type=registry,ref=docker.io/myrepo/myimg \
      --output type=image,name=docker.io/myrepo/myimg,push=true \
      --export-cache type=inline
```

The above uses BuildKit to build a container image from the 
`/workspace/my_container/Dockerfile` file and using `/workspace` as the build 
context. The `$_DOCKER_CONFIG_DIR` substitution is used to point to the 
directory where `buildctl` can find authentication credentials in order to pull 
the container images used as cache, as well as pushing the image produced by 
this step.

And the above workflow is executed by running:

```bash
popper run -f wf.yml -s _DOCKER_CONFIG_DIR=$HOME/.docker/
```

If credentials need to be generated as part of the execution of the workflow, 
the following step can be executed prior to running the BuildKit step:

```yaml
- id: dockerhub login
  uses: docker://docker:19.03
  secrets: [DOCKERHUB_USERNAME, DOCKERHUB_PASSWORD]
  runs: [sh, -ec]
  options:
    volumes:
    - $_DOCKER_CONFIG_DIR:/root/.docker/
  args:
  - |
    docker login -u $DOCKERHUB_USERNAME -p $DOCKERHUB_PASSWORD
```

The above expects `DOCKERHUB_USERNAME` and `DOCKERHUB_PASSWORD` environment 
variables. Alternatively, these can be defined as substitutions:

```yaml
- id: dockerhub login
  uses: docker://docker:19.03
  runs: [sh, -ec]
  options:
    volumes:
    - $_DOCKER_CONFIG_DIR:/root/.docker/
  args:
  - |
    docker login -u $_DOCKERHUB_USERNAME -p $_DOCKERHUB_PASSWORD
```

And executed as:

```bash
popper run -f wf.yml \
  -s _DOCKER_CONFIG_DIR=$PWD/docker-config/ \
  -s _DOCKERHUB_USERNAME=myuser \
  -s _DOCKERHUB_PASSWORD=mypass
```

## Computational research with Python

This guide explains how to use Popper to develop and run reproducible workflows
for computational research in fields such as bioinformatics, machine learning, physics 
or statistics. 
Computational research relies on complex software dependencies that are difficult to port 
across environments. In addition, a typical workflow involves multiple dependent 
steps which will be hard to replicate if not properly documented.
Popper offers a solution to these challenges:
- Poppers abstracts over software environments with [Linux containers](https://popper.readthedocs.io/en/latest/sections/concepts.html#glossary).
- Poppers forces you to define your workflow explicetely such that it can be re-run in 
in a single command.

Popper thus provides an open-source alternative to managed solutions such as
Code Ocean for reproducible computational research.

### Pre-requisites

You should have basic knowledge of:
- git
- command line 
- Python

In addition, you should be familiar with the concepts introduced in the 
[Getting Started](https://popper.readthedocs.io/en/latest/sections/getting_started.html)
section.
This guide uses examples from machine learning but no prior knowledge of the field
is required.


### Getting started

The examples presented in this guide come from a workflow developed for the 
[Flu Shot Learning](https://www.drivendata.org/competitions/66/flu-shot-learning/) 
research competition on Driven Data.
This workflow shows examples of using Popper to automate common tasks in computational
research:
- downloading data
- using a Jupyter notebook
- fitting/simulating a model
- visualizing the results
- generating a paper with up-to-date results

To help follow allong, see this 
[repository](https://github.com/getpopper/popper-examples/tree/master/workflows/comp-research/python) with the final version of the workflow.
To adapt the advice in this guide to your own project, get started
with this [Cookiecutter template for Popper](https://github.com/getpopper/cookiecutter-popper-python).


Initial project structure:
```
├── LICENSE                                 
├── README.md                <- The top-level README.
├── data                     <- The original, immutable data dump.
├── results             
|   ├── models               <- Serialized models, predictions, model summaries.
|   └── figures              <- Graphics created during analysis.
├── paper                    <- Generated analysis as PDF, LaTeX.
│   ├── paper.tex
|   └── referenced.bib
└── src                      <- Python source code for this project.
    ├── notebooks            <- Jupyter notebooks.
    ├── get_data.sh          <- Script for downloading the original data dump.
    ├── models.py            <- Script defining models.
    ├── predict.py           <- Script for generating model predictions.
    └── evaluate_model.py    <- Script for generating model evaluation plots.
```    

### Getting data

Your workflow should automate downloading or generating data to ensure that it uses the correct,
up-to-date version of the data. In this example, you can download data with a 
simple shell script:

```sh
#!/bin/sh
cd $1

wget "https://s3.amazonaws.com/drivendata-prod/data/66/public/test_set_features.csv" --no-check-certificate
wget "https://s3.amazonaws.com/drivendata-prod/data/66/public/training_set_labels.csv" --no-check-certificate
wget "https://s3.amazonaws.com/drivendata-prod/data/66/public/training_set_features.csv" --no-check-certificate

echo "Files downloaded: $(ls)"
```

Now, wrap this step using a Popper workflow. In a new file `wf.yml` at the root 
of the folder,

```yaml
steps:
- id: "dataset"
  uses: "docker://jacobcarlborg/docker-alpine-wget"
  args: ["src/get_data.sh", "data"]
```
Notes:
- pick a Docker image that contains the necessary utilities. 
For instance, a default Alpine image does not include `wget`.


### Using JupyterLab

This sections explains how to use Popper to launch Jupyter notebooks, which are a
 useful tool for exploratory work.
Refactoring successful experiments into your final workflow is easier if you keep
the software environment consistent between both, which you can do by defining a
container shared between steps.

Some workflows will require multiple containers (and `Dockerfiles`), so it is
 good practice to organize these from the start in a seperate folder.
In `containers/`, create this `Dockerfile`:

```Dockerfile
FROM continuumio/miniconda3:4.8.2
ENV PYTHONDONTWRITEBYTECODE=true 
# update conda environment with packages and clean up conda installation by removing 
# conda cache/package tarbarlls and python bytecode
COPY environment.yml .
RUN conda env update -f exploration_env.yml \
    && conda clean -afy \
    && find /opt/conda/ -follow -type f -name '*.pyc' -delete 
CMD [ "/bin/sh" ] 
```

Use a separate `environment.yml` file to define your Python environment. This
avoids modifying the `Dockerfile` manually each time you need a new Python package.
Create `containers/environment.yml`:

```yaml
name: base
channels:
  - conda-forge
  - base
dependencies:
  - jupyterlab=1.0
```

To launch JupyterLab, first add a new step to your workflow in `wf.yml`
```yaml
- id: "notebook"
  uses: "./containers/"
  args: ["jupyter", "--version"] 
  options: 
    ports: 
      8888/tcp: 8888
```

Notes:
- `uses` is set to `./containers/` which tells Popper where to find the `Dockerfile`
 defining the container used for this step
- `ports` is set to `{8888/tcp: 8888}` which is necessary for the host machine to connect
 to the Jupyter Lab server in the container

Next, in the local command line, execute the `notebook` step in interactive mode:
```sh
popper sh -f wf.yml notebook
```
Now, in the Docker container's command line:
```sh
jupyter lab --ip 0.0.0.0 --no-browser --allow-root 
```
Skip this second step if you only need the shell interface.

Notes:
- `--ip 0.0.0.0` allows the user to access JupyterLab from outside the container (by default, 
Jupyter only allows access from `localhost`).
- `--no-browser` tells jupyter to not expect to find a browser in the docker container.
- `--allow-root` runs JupyterLab as a root user (the recommended method for running Docker
 containers), which is not enabled by default.

Open the generated link in a browser to access JupyterLab.

### Package management

It can be difficult to guess in advance which software libraries are needed in
the final workflow. 
Instead, update the workflow requirements as you go using one of the package managers 
available for Python.

#### conda
 
Conda is recommended for package management because it has better dependency
 management and support for compiled libraries. 
When executing the `notebook` step interactively, install package as needed using
(the easiest way to access the container's command line in this situation is 
Jupyter Lab's terminal interface):

```bash
conda install PACKAGE [PACKAGE ...]
```

Update the environment requirements with:

``` bash
conda env export > containers/environment.yml
```

On the next use of the Docker image, Popper will rebuild it with the updated 
requirements 
(Note: this is triggered by` COPY environment.yml` in the `Dockerfile`).

#### pip

You can adapt the process decribed for `conda` to `pip`:

```bash
pip install PACKAGE [PACKAGE ...]
pip freeze > containers/requirements.txt
```
Modify the run command `RUN` in the `Dockerfile` to:
```dockerfile
RUN pip install -r requirements.txt
```

#### Seperating docker images

Some workflows have conflicting software requirements between steps, for instance if two
 steps require different versions of a library. In this case, organize your container
 definitions as follows:

```
└── containers
    ├── step_A 
    |   ├── Dockerfile
    |   └── environment.yml
    └── step_B
        ├── Dockerfile
        └── environment.yml
```

Then, in  `wf.yml`:

```yaml
- id: "step_A"
  uses: "./containers/step_A/"
# ...

- id: "step_b"
  uses: "./containers/step_B/
```


### Models and visualization

Following the above, automate the other steps in your workflow using Popper. 
This section shows examples for:
- fitting a model to data 
- generating model evaluation plots
- using the model to make predictions on a hold-out dataset

A first file, `src/models.py` defines the model this workflow uses:

```python
from sklearn import impute, preprocessing, compose, pipeline, linear_model, multioutput

def _get_preprocessor(num_features , cat_features):

    num_transformer = pipeline.Pipeline([
        ("scale", preprocessing.StandardScaler()),
        ("impute", impute.KNNImputer(n_neighbors = 10)),
    ])

    cat_transformer = pipeline.Pipeline([
        ("impute", impute.SimpleImputer(strategy = "constant", fill_value = "missing")),
        ("encode", preprocessing.OneHotEncoder(drop = "first")),
    ])

    preprocessor = compose.ColumnTransformer(
        [("num", num_transformer, num_features), 
        ("cat", cat_transformer, cat_features)
    ])
    return preprocessor

def get_lr_model(num_features, cat_features, C = 1.0):

    model = pipeline.Pipeline([
        ("pre", _get_preprocessor(num_features, cat_features)),
        ("model", multioutput.MultiOutputClassifier(
                    linear_model.LogisticRegression(penalty="l1", C = C, solver = "saga")
        )),
    ])
    return model

```

A second script, `src/predict.py`, uses this model to generate the predictions
on the hold-out dataset:

 ```python
import pandas as pd
import os
from models import get_lr_model

DATA_PATH = "data/raw"
PRED_PATH = "results/predictions"

if __name__ == "__main__":

    X_train = pd.read_csv(os.path.join(DATA_PATH, "training_set_features.csv")).drop(
        "respondent_id", axis = 1
    )

    X_test = pd.read_csv(os.path.join(DATA_PATH, "test_set_features.csv")).drop(
        "respondent_id", axis = 1
    )

    y_train = pd.read_csv(os.path.join(DATA_PATH, "training_set_labels.csv")).drop(
        "respondent_id", axis = 1
    )

    sub = pd.read_csv(os.path.join(DATA_PATH, "submission_format.csv"))

    num_features = X_train.columns[X_train.dtypes != "object"].values
    cat_features = X_train.columns[X_train.dtypes == "object"].values

    model = get_lr_model(num_features, cat_features, 1)
    model.fit(X_train, y_train)
    preds = model.predict_proba(X_test)

    sub["h1n1_vaccine"] = preds[0][:, 1]
    sub["seasonal_vaccine"] = preds[1][:, 1]
    sub.to_csv(os.path.join(PRED_PATH, "baseline_pred.csv"), index = False)
 ```

Add this script as a step in the Popper workflow. This must come after the `get_data` 
step

```yaml
- id: "predict"
  uses: "./containers/"
  args: ["python", "src/predict.py"]
```

Notes:
- This use the same container as in the `notebook` step. Again, the final, 'canonical' 
analysis should be developed in the same environment as exploratory code.

Similarly, add the `src/evaluate_model.py`, which generates model plots, to
the workflow.

```python
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
import os
import pandas as pd
import seaborn as sns
from sklearn.model_selection import cross_val_score
from models import get_lr_model

DATA_PATH = "data/raw"
FIG_PATH = "output/figures"

if __name__ == "__main__":
    mpl.rcParams.update({"figure.autolayout": True, "figure.dpi": 150})
    sns.set()

    X_train = pd.read_csv(os.path.join(DATA_PATH, "training_set_features.csv")).drop(
        "respondent_id", axis=1
    )
    y_train = pd.read_csv(os.path.join(DATA_PATH, "training_set_labels.csv")).drop(
        "respondent_id", axis=1
    )

    num_features = X_train.columns[X_train.dtypes != "object"].values
    cat_features = X_train.columns[X_train.dtypes == "object"].values

    Cs = np.logspace(-2, 1, num = 10, base = 10)
    auc_scores = cross_val_score(
        estimator = get_model(num_features, cat_features, C),
        X = X_train,
        y = y_train,
        cv = 5,
        n_jobs = -1,
        scoring = "roc_auc",
    )

    fig, ax = plt.subplots()
    ax.plot(Cs, auc_scores)
    ax.vlines(
      Cs[np.argmax[auc_scores]], 
      ymin = 0.82, 
      ymax = 0.86, 
      colors = "r", 
      linestyle = "dotted"
    )
    ax.annotate(
      "$C = 0.464$ \n ROC AUC ={:.4f}".format(np.max(auc_scores)), 
      xy = (0.5, 0.835)
    )
    ax.set_xscale("log")
    ax.set_xlabel("$C$")
    ax.grid(axis = "x")
    ax.legend(["AUC", "best $C$"])
    ax.set_title("AUC for different values of $C$")
    fig.savefig(os.path.join(FIG_PATH, "lr_reg_performance.png"))
```

Use a similar step to the previous one:

```yaml
- id: "figures"
  uses: "./"
  args: ["python, src/evaluate_model.py"]
```

Note that these steps each read data from `data/` and output to `results/`.
It is good practice to keep the input and outputs of a workflow separate
to avoid accidently modifying the original data, which is considered immutable.

### Building a paper using LaTeX

Wrap the build of the paper in your Popper workflow.
This is useful to ensure that the pdf is always built with the most up-to-date data 
and figures.

```yaml
- id: "paper"
  uses: "docker://blang/latex:ctanbasic"
  args: ["latexmk", "-pdf", "paper.tex"]
  dir: "/workspace/paper"
```

Notes:
- This step uses a basic LaTeX installation. For more sophisticated needs,
use a [full TexLive image](https://hub.docker.com/r/blang/latex/tags) 
- `dir` is set to `workspace/paper` so that Popper looks for and outputs files in the `paper/` folder


### Conclusion

This is the final workflow:
```yaml
steps:
- id: "dataset"
  uses: "docker://jacobcarlborg/docker-alpine-wget"
  args: ["sh", "src/get_data.sh", "data"]
 
- id: "notebook"
  uses: "./"
  args: ["jupyter", "--version"] 
  options: 
    ports: 
      8888/tcp: 8888

- id: "predict"
  uses: "./"
  args: ["python, src/predict.py"]
    
- id: "figures"
  uses: "./"
  args: ["python, src/evaluate_model.py"]
    
- id: "paper"
  uses: "docker://blang/latex:ctanbasic"
  args: ["latexmk", "-pdf", "paper.tex"]
  dir: "/workspace/paper"
```

And this is the final project structure:
```
├──LICENSE                                 
├── README.md                <- The top-level README.
├── wf.yml                   <- Definition of the workflow.
├── containers               
|   ├── Dockerfile           <- Definition of the OS environment.
|   └── environment.yml      <- Definition of the Python environment.
├── data                     <- The original, immutable data dump.
├── results             
|   ├── models               <- Serialized models, predictions, model summaries.
|   └── figures              <- Graphics created during analysis.
├── paper                    <- Generated analysis as PDF, LaTeX.
│   ├── paper.tex
|   └── referenced.bib
└── src                      <- Python source code for this project.
    ├── notebooks            <- Jupyter notebooks.
    ├── get_data.sh          <- Script for downloading the original data dump.
    ├── models.py            <- Script defining models.
    ├── predict.py           <- Script for generating model predictions.
    └── evaluate_model.py    <- Script for generating model evaluation plots.
```

To re-run the entire workflow, use:
```sh
popper run -f wf.yml
```
