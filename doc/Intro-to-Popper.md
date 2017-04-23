Over the last decade software engineering and systems administration 
communities (also referred to as DevOps) have developed sophisticated 
techniques and strategies to ensure “software reproducibility”, i.e. 
the reproducibility of software artifacts and their behavior using 
versioning, dependency management, containerization, orchestration, 
monitoring, testing and documentation. The key idea behind the Popper 
Convention is to manage every experiment in computation and data 
exploration as a software project, using tools and services that are 
readily available now and enjoy wide popularity. By doing so, 
scientific explorations become reproducible with the same convenience, 
efficiency, and scalability as software reproducibility while fully 
leveraging continuing improvements to these tools and services. Rather 
than mandating a particular set of tools, the convention only expects 
components of an experiment to be scripted. There are two main goals 
for Popper:

 1. It should be usable in as many research projects as possible, 
    regardless of their domain.
 2. It should abstract underlying technologies without requiring a 
    strict set of tools, making it possible to apply it on multiple 
    toolchains.

# A DevOps Approach to Carrying Out Experiments

A common generic workflow for experiments with a computational 
component is the one shown below. Although there are some projects or 
papers that don't fit this description we focus on this model since it 
covers a large portion of experiments out there. The implementation 
and documentation of an experiment, is commonly done in an ad-hoc way 
(custom bash scripts, storing in local archives, etc.).

![Experimentation Workflow. The analogy of a lab notebook in 
experimental sciences is to document an experiment's evolution. This 
is rarely done and, if done, usually in an ad-hoc way (an actual 
notebook or a text file).](figures/workflow.png)

The idea behind Popper is simple: make an article self-contained by 
including in a code repository the manuscript along with every 
experiment's code, orchestration, inputs, parametrization, results and 
validation. To this end we propose leveraging state-of-the-art 
technologies and applying a DevOps approach to the "implementation" of 
an article.

![DevOps approach to Experiments.](figures/workflow_devops.png)

Popper is a convention (methodology or protocol) to map the components 
of an experimentation workflow to the engineering best-practices that 
are commonly applied in open-source software projects. There are three 
main goals for this convention:

 1. Clearly benefit the individual researcher by improving 
    productivity.
 2. It should be usable in as many research projects as possible, 
    regardless of their domain.
 3. It should abstract the underlying technologies.

If, from the inception of an article, a researcher makes use of the 
DevOps toolbox (e.g., version-control systems, lightweight OS-level 
virtualization, automated multi-node orchestration, continuous 
integration and web-based data visualization), then re-executing and 
validating an experiment becomes practical.

# Popper-compliant Experiments

We say that an experiment is Popper-compliant if its code, 
orchestration, dependencies, results, parameterization and validation 
are self-contained. By self-contained, we mean available in a code 
repository with dependencies available in artifact and data 
repositories. If resources are available, we can execute a 
Popper-compliant (or "popperized") experiment can be executed in its 
entirety. Additionally, the commit log becomes the lab notebook, which 
makes the history of changes made to it available to readers, an 
invaluable tool to learn from others and "stand on the shoulder of 
giants". A "popperized" experiment also makes it easier to advance the 
state-of-the-art, since it becomes easier to extend existing work by 
applying the same model of development in OSS (fork, make changes, 
publish new findings).

A list of popperized experiments is available in the [Popper 
Templates](https://github.com/systemslab/popper/master/tree/templates) 
repository. See [below](#popper-templates-and-the-popper-cli-tool) for 
how to use the Popper-CLI tool to easily explore the templates 
repository and add experiments to a paper repository.

# Popper-compliant Tools

While Popper applies to a wide variety of toolchains, it is not 
universal. We generally require tools to have two basic properties:

 1. Referenceable assets. Ability to associate IDs to assets (code, 
    binaries, configuration and data).
 2. Scriptability. The tool in question has to be amenable to 
    automation (scriptable). In general, given a high-level, 
    human-readable script (or asset ID), the tool should be able to 
    act upon it.

The notion of Popper-compliance closely resembles the high-level 
guidelines of the [Twelve-Factor App](http://12factor.net/), 
re-purposed for an academic setting, i.e. we aim for the 
_Twelve-factor Experiment_.

# Repository Structure

The general repository structure is simple: a `paper` and an 
`experiments` folder on the root of the project with one subfolder per 
experiment. Both, article and experiments, if Popper-compliant, can be 
automatically generated and executed, respectively. For an example of 
what a Popper repo looks like, we show one that makes use of Docker, 
Ansible, and Jupyter for an experiment, and Markdown for the 
manuscript:

```bash
$> tree paper-repo/
README.md
experiments/
  an-experiment/
    README.md
    ansible.cfg
    main.yml
    notebook.ipynb
    parameters
    results.csv
    roles/
      baseliner
      monitoring
    run.sh
    visualize.sh
paper/
  build.sh
  citations.bib
  figures/
    an-experiment-result.png
  paper.md
```

The `experiments` folder contains an experiment implemented in Ansible 
that makes use of Docker to obtain the binary dependencies. The 
results are stored in a `.csv` file and analyzed/graphed using Jupyter 
(`notebook.ipynb` file). The experiment parameters (to Ansible) are 
provided in the `parameters` file. The `run.sh` script executes the 
experiment (invokes Ansible) while the `visualize.sh` script instantiates 
a Jupyter server and opens a browser to interact with the notebook in 
real-time. At the end of the execution of the experiment, the figure 
(`an-experiment-result.png`) is regenerated. The article is written in 
Markdown and, using pandoc (in a docker container), it is converted to 
PDF when the `paper/build.sh` script is invoked.

Popper can be applied to other toolchains, not just the ones used in 
this example. A list of "popperized" experiment and manuscript 
templates is available in the [Popper 
Templates](https://github.com/systemslab/popper) repository. The 
[Popper-CLI](https://github.com/systemslab/popper/tree/master/popper) 
tool makes it easy to retrieve templates and add them to a paper 
repository.
