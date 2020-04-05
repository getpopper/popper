from click.testing import CliRunner
import unittest
from popper_test import PopperTest
import popper.commands.cmd_run as run
import unittest
import os
import subprocess
import sys
import stat


class TestSh(unittest.TestCase, PopperTest):

	def test_sh(self):

		workflow_file_loc = self._wfile("sh-wf1","workflow")
		runner = CliRunner()

		with self.assertLogs('popper') as test:
			result = runner.invoke(run.cli, ['--wfile', workflow_file_loc])
			assert result.exit_code == 0

		script_src = os.getcwd() + '/cli/test/fixtures/sh-script'

		os.chmod(script_src, 0o777)

		workflow_file_loc = self._wfile("sh-wf2","workflow")


		runner = CliRunner()
		
		with self.assertLogs('popper') as test:

			result = runner.invoke(run.cli, ['--wfile', workflow_file_loc])
			assert result.exit_code == 0

		if('STEP_INFO:popper:Hello from Popper' in test.output):

			assert 0 == 0

		else:
			assert 0 == 1






