import os
from popper import utils


class ReadMe:
    def __init__(self):
        self.repo_name = utils.get_repo_name()

    def write_readme(self, content, path):
        with open(os.path.join(path, 'README.md'), 'w') as f:
            f.write(content)

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
        content = """
# `{}`
<!--
NOTE: replace all the **TODO** marks with your own content.
-->
"""
        content = content.format(pipeline_name)
        if (len(stages)) > 0:
            content += """
**TODO**: insert high-level description of the pipeline. It consists of the following stages:
"""
            for i, stage in enumerate(stages.split(',')):
                    content += """
* [`{0}`](./{0}.sh). **TODO**. Add high-level description of stage `{0}`.
"""
                    content = content.format(stage)

        content += """

# Obtaining the pipeline

To add this pipeline to  the [`popper` CLI tool](https://github.com/systemslab/popper):

```bash
cd your-repo
popper add org/{0}/{1}
```

**TODO**: replace `org` appropriately.

# Running the pipeline

To run the pipeline using the [`popper` CLI tool](https://github.com/systemslab/popper):

```bash
cd {0}
popper run {1}
```
"""
        content = content.format(self.repo_name, pipeline_name)

        content += """
The pipeline can be executed on the following environment(s):
"""
        for env in envs:
            content += """
* `{}`.
"""
            content = content.format(env)

        content += """
---
The pipeline expects the following environment variables:

* `<ENV_VAR1>`. Description of environment variable.
* `<ENV_VAR2>`. Description of environment variable.

For example, the following is an execution with all expected
variables:
"""
        content += """
```bash
export <ENV_VAR1>=value-for-<ENV_VAR_1>
export <ENV_VAR2>=value-for-<ENV_VAR_2>

popper run {}
```
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
