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

        wf_data = {"steps": [{"uses": "foo",}]}
        wf = WorkflowParser.parse(wf_data=wf_data)

        self.assertEqual("foo", wf.steps[0].uses)


# TODO add missing tests:
# - test_add_missing_ids
# - test_apply_substitutions
# - test_skip_tests
# - test_filter_step
