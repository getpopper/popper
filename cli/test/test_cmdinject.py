from click.testing import CliRunner
import unittest
from popper_test import PopperTest
import popper.commands.cmd_run as run
import unittest
import os
import subprocess
import sys


class TestInject(unittest.TestCase, PopperTest):

	def test_inject(self):

		workflow_file_loc = self._wfile("inject-main", "workflow")
		runner = CliRunner()
		pre_workflow_loc = self._wfile("inject-pre", "workflow")
		post_workflow_loc = self._wfile("inject-post", "workflow")

		os.environ['POPPER_PRE_WORKFLOW_PATH'] = pre_workflow_loc
		os.environ['POPPER_POST_WORKFLOW_PATH'] = post_workflow_loc
		
		result = runner.invoke(run.cli, ['--wfile', workflow_file_loc,'--dry-run'])
		assert result.exit_code == 0

		result = runner.invoke(run.cli, ['--wfile', workflow_file_loc,'--dry-run'])
		assert result.exit_code == 0