import os
import tempfile

from click.testing import CliRunner

from popper.cli import log
from popper.commands import cmd_scaffold, cmd_run
from popper.parser import Workflow

from .test_common import PopperTest


class TestScaffold(PopperTest):
    def setUp(self):
        log.setLevel("CRITICAL")

    def test_scaffold(self):

        wf_dir = tempfile.mkdtemp()
        runner = CliRunner()
        file_loc = f"{wf_dir}/wf.yml"

        result = runner.invoke(cmd_scaffold.cli, ["-f", file_loc])

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
            result = runner.invoke(cmd_run.cli, ["-f", file_loc, "-w", wf_dir])
            self.assertEqual(result.exit_code, 0)
            self.assertTrue(len(test_logger.output))
            self.assertTrue(
                "INFO:popper:Step '1' ran successfully !" in test_logger.output
            )
            self.assertTrue(
                "INFO:popper:Step '2' ran successfully !" in test_logger.output
            )
