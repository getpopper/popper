# Introduction to Popper Pipelines

Over the last decade software engineering and systems administration 
communities (also referred to as DevOps) have developed sophisticated 
techniques and strategies to ensure “software reproducibility”, i.e. 
the reproducibility of software artifacts and their behavior using 
versioning, dependency management, containerization, orchestration, 
monitoring, testing and documentation. The key idea behind the Popper 
protocol is to manage every experiment in computation and data 
exploration as a software project, using tools and services that are 
readily available now and enjoy wide popularity. By doing so, 
scientific explorations become reproducible with the same convenience, 
efficiency, and scalability as software repeatable while fully 
leveraging continuing improvements to these tools and services. Rather 
than mandating a particular set of tools, the convention only expects 
components of an experiment to be scripted. There are two main goals 
for Popper:

 1. It should be usable in as many research projects as possible, 
    regardless of their domain.
 2. It should abstract underlying technologies without requiring a 
    strict set of tools, making it possible to apply it on multiple 
    toolchains.

## Popper Pipelines: A SciOps Approach to Carrying Out Scientific Explorations

A common generic analysis/experimentation workflow involving a 
computational component is the one shown below. We refer to this as a 
pipeline in order to abstract from experiments, simulations, analysis 
and other type of scientific exploration. Although there are some 
projects that don't fit this description, we focus on this model since 
it covers a large portion of pipelines out there. The implementation 
and documentation of a pipeline is commonly done in an ad-hoc way 
(custom bash scripts, storing in local archives, etc.).

![Experimentation Workflow. The analogy of a lab notebook in 
experimental sciences is to document an experiment's evolution. This 
is rarely done and, if done, usually in an ad-hoc way (an actual 
notebook or a text file).](/figures/workflow.png)

The idea behind Popper is simple: make an article self-contained by 
including in a code repository the manuscript along with every 
experiment's scripts, inputs, parametrization, results and validation. 
To this end we propose leveraging state-of-the-art technologies and 
applying a DevOps approach to the implementation of scientific 
pipelines (also referred to SciOps).

![DevOps approach to Implementing Scientific 
Explorations.](/figures/workflow_devops.png)

Popper is a convention (methodology or protocol) to map the components 
found in pipelines to the engineering best-practices that are commonly 
applied in open-source software projects. If, from the inception of an 
article, a researcher makes use of the DevOps toolbox (e.g., 
version-control systems, lightweight OS-level virtualization, 
automated multi-node orchestration, continuous integration and 
web-based data visualization), then re-executing and validating an 
experiment becomes practical.

## Popper-compliant Pipelines

We say that a pipeline is Popper-compliant if its scripts, 
dependencies, parameterization, results and validations are all in the 
same respository (i.e., the pipeline is self-contained). If resources 
are available, we should be able to re-execute a Popper-compliant
("popperized") pipeline in its entirety. Additionally, the commit log 
becomes the lab notebook, which makes the history of changes made to 
it available to readers, an invaluable tool to learn from others and 
"stand on the shoulder of giants". A "popperized" pipeline also makes 
it easier to advance the state-of-the-art, since it becomes easier to 
extend existing work by applying the same model of development in OSS 
(fork, make changes, publish new findings).

## Repository Structure

The general repository structure is simple: a `paper` and a 
`pipelines` folder on the root of the project with one subfolder per 
pipeline

```bash
$> tree mypaper/
├── experiments
│   ├── exp1
│   │   ├── README.md
│   │   ├── output
│   │   │   ├── exp1.csv
│   │   │   ├── post.sh
│   │   │   └── view.ipynb
│   │   ├── run.sh
│   │   ├── setup.sh
│   │   ├── teardown.sh
│   │   └── validate.sh
│   ├── analysis1
│   │   ├── README.md
│   │   └── ...
│   └── analysis2
│       ├── README.md
│       └── ...
└── paper
    ├── build.sh
    ├── figures/
    ├── paper.tex
    └── refs.bib
```

## Pipeline Folder Structure

A minimal pipeline folder structure for an experiment or analysis is 
shown below:

```{#lst:repo .bash caption="Basic structure of a Popper repository."}
$> tree -a paper-repo/pipelines/myexp
paper-repo/pipelines/myexp/
|-- README.md
|-- run.sh
|-- setup.sh
|-- validate.sh
|-- teardown.sh
```

Every pipeline has `setup.sh`, `run.sh` and `validate.sh` scripts that 
serve as the interface to the pipeline. All these return non-zero exit 
codes if there's a failure. In the case of `validate.sh`, this script 
should print to standard output one line per validation, denoting 
whether a validation passed or not. In general, the form for 
validation results is `[true|false] <statement>` (see examples below).

```{#lst:validations .bash caption="Example output of validations."}
[true]  algorithm A outperforms B
[false] network throughput is 2x the IO bandwidth
```

The [CLI](https://github.com/systemslab/popper/popper) tool includes a 
`pipeline init` subcommand that can be executed to scaffold a pipeline 
with the above structure. The syntax of this command is the following:

```bash
popper pipeline init <name>
```

Where `<name>` is the name of the pipeline to initialize. More details 
on how pipelines are executed is presented in the next section.
