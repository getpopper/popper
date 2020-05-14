import unittest
import os

from popper.parser import WorkflowParser
from popper.cli import log

import logging


class TestWorkflow(unittest.TestCase):
    def setUp(self):
        log.setLevel("CRITICAL")

    def tearDown(self):
        log.setLevel("NOTSET")

    def test_new_workflow(self):
        wf_data = {}
        self.assertRaises(SystemExit, WorkflowParser.parse, **{"wf_data": wf_data})

        wf_data = {"unexpected": []}
        self.assertRaises(SystemExit, WorkflowParser.parse, **{"wf_data": wf_data})

        wf_data = {
            "steps": [
                {"uses": "foo", "id": "step", "env": {"EN": "EE"}, "secrets": ["S"]},
                {"uses": "bar", "runs": ["a", "b"], "args": ["c"], "skip_pull": True},
            ],
            "options": {"env": {"FOO": "bar"}, "secrets": ["Z"]},
        }
        wf = WorkflowParser.parse(wf_data=wf_data)

        step = wf.steps[0]
        self.assertEqual("step", step.id)
        self.assertEqual("foo", step.uses)
        self.assertEqual(("Z", "S"), step.secrets)
        self.assertEqual({"EN": "EE", "FOO": "bar"}, step.env)
        self.assertTrue(not step.runs)
        self.assertTrue(not step.args)
        self.assertFalse(step.skip_pull)

        step = wf.steps[1]
        self.assertEqual("bar", step.uses)
        self.assertEqual(("a", "b"), step.runs)
        self.assertEqual(("c",), step.args)
        self.assertTrue(step.skip_pull)
        self.assertEqual({"FOO": "bar"}, step.env)
        self.assertEqual(("Z",), step.secrets)

        self.assertEqual({"FOO": "bar"}, wf.options.env)
        self.assertEqual(("Z",), wf.options.secrets)


# TODO add tests for:
# - test_add_missing_ids
# - test_apply_substitutions
# - test_skip_tests
# - test_filter_step
