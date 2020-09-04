import os

from popper import __version__
from popper.cli import log
from popper.exporter import WorkflowExporter

from .test_common import PopperTest


class TestExporter(PopperTest):
    @classmethod
    def setUpClass(self):
        log.setLevel("CRITICAL")

    def test_get_matrix_variables(self):
        given = ["_A=a1", "_A=a2", "_B=b1", "_B=b2", "_B=b3", "_C=c1"]
        expected = {
            "A": ["a1", "a2"],
            "B": ["b1", "b2", "b3"],
            "C": ["c1"],
        }
        self.assertEqual(expected, WorkflowExporter._get_matrix_variables(given))
        self.assertEqual({}, WorkflowExporter._get_matrix_variables([]))

    def test_get_matrix(self):
        given = {
            "A": ["a1", "a2"],
            "B": ["b1", "b2", "b3"],
            "C": ["c1"],
        }
        expected = [
            {"A": "a1", "B": "b1", "C": "c1"},
            {"A": "a1", "B": "b2", "C": "c1"},
            {"A": "a1", "B": "b3", "C": "c1"},
            {"A": "a2", "B": "b1", "C": "c1"},
            {"A": "a2", "B": "b2", "C": "c1"},
            {"A": "a2", "B": "b3", "C": "c1"},
        ]
        self.assertEqual(expected, list(WorkflowExporter._get_matrix(given)))

    def test_travis(self):
        subs = ["_A=a1", "_A=a2", "_B=b1", "_B=b2", "_B=b3", "_C=c1"]
        repo = self.mk_repo()
        pwd = os.getcwd()
        os.chdir(repo.working_dir)
        e = WorkflowExporter.get_exporter("travis")
        e.export("wf.yml", subs)
        self.assertTrue(os.path.isfile(".travis.yml"))

        expected_env_items = [
            "A=a1 B=b1 C=c1",
            "A=a1 B=b2 C=c1",
            "A=a1 B=b3 C=c1",
            "A=a2 B=b1 C=c1",
            "A=a2 B=b2 C=c1",
            "A=a2 B=b3 C=c1",
        ]

        with open(".travis.yml", "r") as f:
            content = f.read()
            for e in expected_env_items:
                self.assertTrue(e in content)

            self.assertTrue("-s _A=$A -s _B=$B -s _C=$C" in content)

            self.assertTrue(f"getpopper/popper:v{__version__}" in content)

        os.chdir(pwd)
