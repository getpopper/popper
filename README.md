# The Popper Convention

> Treating Academic Papers as Code Projects

This project describes a convention for generating falsifiable 
research. There are two main goals:

 1. It should apply to as many research projects as possible, 
    regardless of their domain.
 2. It should "work", regardless of the underlying technologies; if 
    not, there's a bug in the convention.

In the following, I use `git` as the VCS, `docker` as the experiment 
execution substrate, `ansible` as the experiment orchestrator and 
`scipy` for analysis/visualization. As stated in goal 2, any of these 
should be swappable for other tools, for example: VMs instead of 
docker; puppet instead of ansible; R insted of scipy; and so on and so 
forth.

## Convention For Organizing Files

  * The structure of a "paper repo" is the following:

    ```
    paper/
      experiments/
        exp1/
          assertions.aver
          fig1.png
          inventory
          notebook.ipynb
          output.csv
          playbook.yml
          vars.yml
          run.sh
      build.sh
      main.md
    ```

  * A paper is written in any desired format. Here we use markdown as 
    an example (`main.md`).

  * There is a `build.sh` command that generates the output format 
    (e.g. `PDF`).

  * Every experiment in the paper has a corresponding folder in the 
    repo. For example, `exp1` referred in a paper, there is a 
    `experiments/exp1/` folder in the repo.

  * Every figure in the paper has a `[source]` link in its caption 
    that points to the URL of the corresponding experiment folder in 
    the web interface of the VCS (e.g. github).

  * `notebook.ipynb` contains the notebook that, at the very least, 
    displays the figures for the experiment. It can serve as an 
    "extended" version of what figures in the paper display, including 
    other figures that contain analysis that show similar results. If 
    the repo is checked out locally into another person's machine, 
    it's a nice way of having readers play with the result's data 
    (although they need to know how to instantiate a local notebook 
    server).

  * If desired, the experiment can be re-executed. The high-level data 
    flow is the following:

    ```
      edit(inventory) -> invoke(run.sh) ->
        ansible(pull_docker_images) ->
        ansible(run_docker_images) ->
        fetch(output, facts, etc) ->
        postprocess ->
        genarate_image ->
        aver_assertions
    ```

    Thus, the absolutely necessary files are `run.sh` which bootstraps 
    the experiment (by invoking a containerized ansible); `inventory`, 
    `playbook.yml` and `vars.yml` which are given to ansible.

    The execution of the experiment will produce output that is either 
    consumed by a postprocessing script, or directly by the notebook. 
    The output can be in any format (CSVs, HDF, NetCDF, etc.).

  * `output.csv` is the ultimate output of the experiment and what it 
    gets displayed in the notebook.

  * `playbook.yml`, `inventory`, `vars.yml`. Files for `ansible`. An 
    important component of the playbook is that it should `assert` the 
    environment and corroborate as much assumptions as possible (e.g. 
    via the `assert` task). `vars.yml` contains the parametrization of 
    the experiment.

  * `assertions.aver`. An optional file that contains assertions on 
    the output data in the _aver_ language.

## Convention For Paper Dependencies

Dependencies can be tracked via submodules (e.g. placed in the 
`vendor/` folder).

### Executables

For every execution element in the high-level script, there is a repo 
that has the source code of the executables, and an artifact repo that 
holds the output of the "pointed-to" version. In our example, we use 
git and docker. So, let's say the execution that resulted in `fig1` 
refers to code of a `foo` codebase. Then:

  * there's a git repo for foo and there's a tag/sha1 that we refer to 
    in the paper repo.

  * for the version that we are pointing to, there is a docker image 
    in the docker hub. E.g. if foo#tag1 is what we refer to, then 
    there's a docker image <repo>/foo:tag1. We can optionally track 
    the image's source (dockerfile) with submodules.

# Examples

  * [VarSys16](https://github.com/ivotron/varsys16)

# Related Work

In [@dolfi_model_2014], the authors introduce a "paper model" of 
reproducible research. We are generalizing this by introducing binary 
reproducibility (docker images) and experiment orchestration 
(ansible).
