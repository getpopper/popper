import os
import popper.utils as pu


class ReadMe:
    def __init__(self):
        self.project_root = pu.get_project_root()
        self.repo_name = pu.infer_repo_name_from_root_folder()

    def write_readme(self, content, path):
        """ Creates a README.md file with the specified content
        at the given path.

        Args:
            content (str): The contents for the README.md file
            path (str): The absolute path where the README.md file
                        is to be created,
        """

        with open(os.path.join(path, 'README.md'), 'w') as f:
            f.write(content)

    def init_project(self):
        content = """# {0}

This repository contains [Popper](https://github.com/systemslab/popper)
pipelines. To show a list of available pipelines using the
[`popper` CLI tool](https://github.com/systemslab/popper):

```bash
cd {0}
popper ls
```

to execute one of the pipelines:

```bash
popper run <pipeline-name>
```

where `<pipeline-name>` is one of the pipelines in the repository.
For more on what other information from this repository is available,
you can run:

```bash
popper --help
```
"""
        content = content.format(self.repo_name)
        self.write_readme(content, self.project_root)

    def init_pipeline(self, pipeline_path, stages, envs):
        """ Generates a README template for the newly initialized
        pipeline.

        Args:
            pipeline_path (str): The absolute path of the pipeline.
            stages (str): Contains all the stages of the pipeline separated
                          by comma.
            envs (list): Contains a list of the environments on which the
                         pipeline can be executed.

        """

        pipeline_name = pipeline_path.split('/')[-1]
        content = """# `{}`

<!--
NOTE TO AUTHORS: replace all the **TODO** marks with your own content.
-->
"""
        content = content.format(pipeline_name)
        if (len(stages)) > 0:
            content += """
**TODO**: insert high-level description of the pipeline.

The pipeline consists of the following stages:
"""
            for i, stage in enumerate(stages.split(',')):
                content += """
  * [`{0}`](./{0}.sh). **TODO**: describe `{0}` stage.
"""
                content = content.format(stage)

        content += """
# Obtaining the pipeline

To add this pipeline to your project using the
[`popper` CLI tool](https://github.com/systemslab/popper):

```bash
cd your-repo
popper add {0}/{1}/{2}
```
{3}
# Running the pipeline

To run the pipeline using the
[`popper` CLI tool](https://github.com/systemslab/popper):

```bash
cd {1}
popper run {2}
```
"""
        url = pu.get_remote_url()
        if url:
            if 'https://' in url:
                org = os.path.basename(os.path.dirname(url))
            else:
                org = url.split(':')[1]
            todomark = ''
        else:
            org = '<org>'
            todomark = '**TODO**: replace `org` appropriately.'

        content = content.format(org, self.repo_name, pipeline_name, todomark)

        content += """
The pipeline is executed on the following environment(s): `{}`. In addition,
the following environment variables are expected:

  * `<ENV_VAR1>`. Description of variable.
  * `<ENV_VAR2>`. Another description.

> **TODO**: rename or remove ENV_VAR1 and ENV_VAR2 appropiately.

For example, the following is an execution with all expected
variables:
"""
        content = content.format(','.join(envs))

        content += """
```bash
export <ENV_VAR1>=value-for-<ENV_VAR_1>
export <ENV_VAR2>=value-for-<ENV_VAR_2>

popper run {}
```

> **TODO**: rename or remove `export` statements above appropriately.
"""
        content = content.format(pipeline_name)
        content += """
# Dependencies

**TODO**: add list of dependencies, for example:

  * Python.
  * C++ compiler.
  * [Docker](https://docker.com) (for generating plots).
  * etc.
"""
        self.write_readme(content, pipeline_path)
