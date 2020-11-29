import os
import yaml

from itertools import product

from popper import __version__
from popper.parser import WorkflowParser
from popper.cli import log


class WorkflowExporter(object):
    """Base class for exporters."""

    def __init__(self):
        pass

    def export(self, file, substitution=[]):
        raise NotImplementedError("Needs implementation in derived classes.")

    @staticmethod
    def get_exporter(service_name):
        if service_name == "travis":
            return TravisExporter()
        else:
            raise Exception(f"Unknown service {service_name}")

    @staticmethod
    def _get_matrix_variables(substitution=[]):
        """Given a list of substitutions, where one key can appear multiple 
        times, this function obtains a dictionary with each key corresponding to 
        a key in the substitutions list, and its values being the distinct 
        values that are specified for it. For example, given substitution list:

            ["_A=a1", "_A=a2", "_B=b1", "_B=b2", "_B=b3", "_C=c1"]

        this function returns:

            {
                "A": ["a1", "a2"],
                "B": ["b1", "b2", "b3"],
                "C": ["c1"],
            }
        """
        matrix = {}

        for s in substitution:
            k, v = WorkflowParser.substitution_to_tuple(s)

            # drop the leading underscore
            k = k[1:]

            if k not in matrix:
                matrix[k] = []
            matrix[k].append(v)

        return matrix

    @staticmethod
    def _get_matrix(matrix_variables={}):
        """Returns an iterator of matrix elements. Each element in the matrix is 
        a dictionary, with keys corresponding to the name of the variable, and 
        the (single) value associated to the key representing the value that 
        this variable takes. For example, given the variables:

            {
                "A": ["a1", "a2"],
                "B": ["b1", "b2", "b3"],
                "C": ["c1"],
            }

        returns an iterator for the following:

            [
                {"A": "a1", "B": "b1", "C": "c1"},
                {"A": "a1", "B": "b2", "C": "c1"},
                {"A": "a1", "B": "b3", "C": "c1"},
                {"A": "a2", "B": "b1", "C": "c1"},
                {"A": "a2", "B": "b2", "C": "c1"},
                {"A": "a2", "B": "b3", "C": "c1"},
            ]
        """
        keys, values = zip(*matrix_variables.items())
        for bundle in product(*values):
            yield dict(zip(keys, bundle))


class TravisExporter(WorkflowExporter):
    path = ".travis.yml"
    template = """
dist: xenial

services: docker

env: {jobs}

script: |
  printenv > /tmp/.envfile
  docker run --rm -ti \\
    --volume /tmp:/tmp \\
    --volume /var/run/docker.sock:/var/run/docker.sock \\
    --volume "$PWD":"$PWD" \\
    --workdir "$PWD" \\
    --env-file /tmp/.envfile \\
    getpopper/popper:v{version} run -f {file} {substitution_flags}
"""

    def __init__(self, **kw):
        super(TravisExporter, self).__init__(**kw)

    def export(self, file, substitution=[]):

        matrix_variables = WorkflowExporter._get_matrix_variables(substitution)
        matrix = WorkflowExporter._get_matrix(matrix_variables)

        # generate env list from matrix
        jobs = []
        for e in matrix:
            job = []
            for k, v in e.items():
                job.append(f"{k}={v}")
            jobs.append(" ".join(job))

        # get the substitution flags for popper run
        substitution_flags = []
        for k in matrix_variables.keys():
            substitution_flags.extend(["-s", f"_{k}=${k}"])

        with open(TravisExporter.path, "w") as f:
            f.write(
                TravisExporter.template.format(
                    file=file,
                    version=__version__,
                    jobs=jobs,
                    substitution_flags=" ".join(substitution_flags),
                )
            )
