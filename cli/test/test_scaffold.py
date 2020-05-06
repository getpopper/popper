from click.testing import CliRunner

import popper.commands.cmd_scaffold as scaffold
import popper.commands.cmd_run as run
from test.test_common import PopperTest
from popper.parser import Workflow, YMLWorkflow, HCLWorkflow

import unittest
import os
import tempfile


class TestScaffold(PopperTest):
    def test_scaffold(self):

        wf_dir = tempfile.mkdtemp()
        runner = CliRunner()
        file_loc = f"{wf_dir}/wf.yml"

        result = runner.invoke(scaffold.cli, ["-f", file_loc])

        self.assertEqual(result.exit_code, 0)
        self.assertTrue(os.path.isfile(file_loc))

        wf = Workflow.new(file_loc)
        self.assertDictEqual(
            wf.steps,
            {
                "1": {
                    "uses": "popperized/bin/sh@master",
                    "args": ["ls"],
                    "name": "1",
                    "next": {"2"},
                },
                "2": {
                    "uses": "docker://alpine:3.11",
                    "args": ["ls"],
                    "name": "2",
                    "needs": ["1"],
                },
            },
        )

        with self.assertLogs("popper") as test_logger:

            result = runner.invoke(run.cli, ["-f", file_loc])
            self.assertEqual(result.exit_code, 0)
            self.assertTrue(len(test_logger.output))
            self.assertTrue(
                "INFO:popper:Step '1' ran successfully !" in test_logger.output
            )
            self.assertTrue(
                "INFO:popper:Step '2' ran successfully !" in test_logger.output
            )
