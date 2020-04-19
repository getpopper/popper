from click.testing import CliRunner

import popper.commands.cmd_scaffold as scaffold
import popper.commands.cmd_run as run
from test_common import PopperTest

import unittest
import os


class TestScaffold(PopperTest):

    def test_scaffold(self):

        repo = self.mk_repo()
        runner = CliRunner()
        file_loc = repo.working_dir+'/wf.yml'

        result = runner.invoke(scaffold.cli, ['-f', file_loc])

        self.assertEqual(result.exit_code, 0)
        self.assertTrue(os.path.isfile(file_loc))

        with self.assertLogs('popper') as test_logger:

            result = runner.invoke(run.cli, ['-f', file_loc])
            self.assertEqual(result.exit_code, 0)

        self.assertTrue(len(test_logger.output))
