# Guides

This is a list of guides related to several aspects of working with 
Popper workflows.

### Choosing a location for your step

If you are developing a docker image for other people to use, we 
recommend keeping this image in its own repository instead of bundling
it with your repository-specific logic. This allows you to version, 
track, and release this image just like any other software. Storing a 
docker image in its own repository makes it easier for others to 
discover, narrows the scope of the code base for developers fixing 
issues and extending the image, and decouples the image's versioning 
from the versioning of other application code.

### Using shell scripts to define step logic

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

### Hello world step example

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

```hcl
- uses: docker://byrnedo/alpine-curl:0.1.8
  args: ["scripts/download-data.sh"]

- uses: docker://python:3.7
  args: ["./scripts/get_mean_by_group.py", "5"]

- uses: docker://python:3.7
  args [
    "./scripts/validate_output.py",
    "./data/global_per_capita_mean.csv"
  ]
```

The above workflow runs correctly anywhere where Docker containers can 
run.

[search]: https://hub.docker.com
[create]: https://docs.docker.com/get-started/part2/



## Computational research with Python

This guide explains how to use Popper to develop and run reproducible workflows
in for computational research in fields such as physics, machine learning or
bioinformatics

### Getting started

[TODO: introduction to reproducibility and major concepts in Popper?]

#### Pre-requisites

Basic knowledge of git, command line and Python. It is also 
recommended to read through the rest of the
[documentation](https://popper.readthedocs.io/en/latest/sections/getting_started.html)
for Popper. 

To adapt the recommendations of this guide to your own workflow, fork this 
[template repository]() or use the [Cookiecutter template](). (TODO: fix links)

#### Case study

Thoughout this guide, the  
[Flu Shot Learning](https://www.drivendata.org/competitions/66/flu-shot-learning/) 
research competition on Driven Data is used as an example project for developing the workflow. 
To help follow allong, see the final [repository]() for this workflow.
This example is from machine learning but  knowledge of the field is not essential to this guide.

Initial project structure:
```
├── environment.yml          <- The file defining the conda Python environmentt. 
├── LICENSE                                 
├── README.md                <- The top-level README.
├── data
│   ├── processed            <- The final, canonical data sets for modeling.
│   └── raw                  <- The original, immutable data dump.
├── results             
|   ├── models               <- Serialized models, predictions, model summaries.
|   └── figures              <- Graphics created during analysis.
├── paper                    <- Generated analysis as PDF, LaTeX.
└── src                      <- Source code for this project.
    ├── notebooks            <- Jupyter notebooks.
    ├── get_data.sh
    ├── models.py
    ├── predict.py
    ├── evaluate_model.py 
    └── __init__.py          <- Makes this a python module.
```    

### Downloading data

A computational workflow should automate the acquisition of data to ensure
that the correct version of the data is used.
In our example, this can be done with a python script

```sh
#!/bin/sh
cd data/raw

wget "https://s3.amazonaws.com/drivendata-prod/data/66/public/test_set_features.csv"
wget "https://s3.amazonaws.com/drivendata-prod/data/66/public/training_set_labels.csv"
wget "https://s3.amazonaws.com/drivendata-prod/data/66/public/training_set_features.csv"

echo "Files downloaded:"
ls 
```
Now, wrap this step using a Popper workflow. In `wf.yml`,
```yaml
steps:
  - id: "dataset"
    uses: "docker://jacobcarlborg/docker-alpine-wget"
    runs: ["sh"]
    args: ["src/get_data.sh"]
```
Remarks:
- it is important to ensure that the Docker images contains the necessary utilities. 
For instance, a default Alpine image does not include `wget` 


### Interactive development

Computational research usually has an exploratory phase.
To make it easier to adapt exploratory work to a final workflow, it is recommended 
to do both in the same environment.

Computational notebooks are a great tool for exploratory work. This sections covers how to 
launch a Jupyter notebook using Popper.

Add a new step to the workflow in `wf.yml`
```yml
  - id: "notebook"
    uses: "./"
    args: ["sh"] 
    options: 
      ports: 
        8888/tcp: 8888
```

Remarks:
- `uses` is set to `./` (current directory), as this step uses an image built from the 
  `Dockerfile` in the local workspace directory
- `ports` is set to `{8888/tcp: 8888}` which will allow the host machine to connect to the notebook server in the container

In your local shell, execute the step in interactive mode
```sh
popper sh -f wf.yml jupyter
```
In the docker container's shell, run
```sh
jupyter lab --ip 0.0.0.0 --no-browser --allow-root 
```
Skip this second step if you only need the shell interface

Remarks:
- `--ip 0.0.0.0` allows the user to access JupyterLab from outside the container (by default, 
Jupyter only allows access from `localhost`)
- `--no-browser` tells jupyter to not expect to find a browser in the docker container
- `--allow-root` allows us to run JupyterLab as a root user (the default user in our Docker
image), which Jupyter does not enable by default

Copy and paste the generated link in the browser on your host machine to access the JupyterLab 
environment.


### Package management

It can be difficult to guess in advance which software libraries will be needed. 
Instead, we recommend updating the workflow requirements as you go using one of 
the package managers available for Python.

#### conda
 
Conda is recommended for managing packages, due to its superior dependency 
management and support for data analysis work. 
While executing the `notebook` step interactively, extra packages can be installed as
needed using 
```bash
conda install PACKAGE [PACKAGE ...]
```
Then save the resulting requirements using 
``` bash
conda env export > environment.yml
```
The next time Popper executes this step, it will rebuild the Docker image with
these new requirements (This is done by copying `environment.yml` in our `Dockerfile`)

#### pip

The workflow described for `conda` can easily be adapted to `pip`. 

```bash
pip install PACKAGE [PACKAGE ...]
pip freeze > requirements.txt
```
Modify the run command `RUN` in the provided `Dockerfile` to
```dockerfile
RUN pip install -r requirements.txt
```

### Models and visualization

Following the above advice, wrap your code for data processing, modeling and generating
figures

In this example generate model diagnostic plots and predictions on the
hold-out test set

Exploratory work yielded the following model
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
    ] )

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
A second script calls this model to generate predictions:

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

Add this script as a step in the Popper workflow. This must be after the `get_data` 
step
```yaml
  - id: "predict"
    uses: "./"
    args: "python src/predict.py"
```
The same Docker container as for the `jupyter` step is used.


Similarly, the script for generating model plots is added to the workflow
```python
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib as mpl

import pandas as pd
import os
import numpy as np

from sklearn.model_selection import cross_validate
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
    means = []
    stds = []
    best_auc = 0
    for C in Cs:
        cv = cross_validate(
            estimator = get_model(C),
            X = X_train,
            y = y_train,
            cv = 5,
            n_jobs = -1,
            scoring = "roc_auc",
        )
        means.append(np.mean(cv["test_score"]))
        stds.append(np.std(cv["test_score"]))
        if means[-1] > best_auc:
            best_C = C
            best_auc = means[-1]

    fig, ax = plt.subplots()
    ax.plot(Cs, means)
    ax.vlines(best_C, ymin = 0.82, ymax = 0.86, colors = "r", linestyle = "dotted")
    ax.annotate("$C = 0.464$ \n ROC AUC = 0.843", xy = (0.5, 0.835))
    ax.set_xscale("log")
    ax.set_xlabel("$C$")
    ax.grid(axis = "x")
    ax.legend(["AUC", "best $C$"])
    ax.set_title("AUC for different values of $C$")
    fig.savefig(os.path.join(FIG_PATH, "lr_reg_performance.png"))
```

With the following step

```yaml
  - id: "figures"
    uses: "./"
    args: "python src/evaluate_model.py"
```

### Building a paper using LaTeX

It is easy to wrap the generation of the final paper in a Popper workflow.
This is  useful to ensure that the paper is always built with the most up-to-date data and figures.

```yaml
  - id: "paper"
    uses: "docker://blang/latex:ctanbasic"
    args: ["pdflatex", "paper.tex"]
    dir: "/workspace/paper"
```

Remarks:
- This step uses a basic LaTeX installation. For more sophisticated needs,
use a full [TexLive image](https://hub.docker.com/r/blang/latex/tags) 
- `dir` is set to `workspace/paper` so that Popper looks for, and outputs files in the `paper` folder


### Conclusion

This is the final workflow
```yaml
steps:
  - id: "dataset"
    uses: "docker://jacobcarlborg/docker-alpine-wget"
    runs: ["sh"]
    args: ["src/get_data.sh"]
 
 - id: "notebook"
   uses: "./"
   rgs: ["sh"] 
   options: 
     ports: 
       8888/tcp: 8888

 - id: "predict"
   uses: "./"
    args: "python src/predict.py"
    
 - id: "figures"
   uses: "./"
   args: "python src/evaluate_model.py"
    
 - id: "paper"
   uses: "docker://blang/latex:ctanbasic"
   args: ["pdflatex", "paper.tex"]
   dir: "/workspace/paper"
```
