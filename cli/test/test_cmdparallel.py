from click.testing import CliRunner
import unittest
from popper_test import PopperTest
import popper.commands.cmd_run as run
import unittest
import os
import subprocess
import sys
import stat


class TestParallel(unittest.TestCase, PopperTest):

	def test_parallel(self):

		workflow_file_loc = self._wfile("parallel-wf1","workflow")
		# runner = CliRunner()
		# result = runner.invoke(run.cli, ['--wfile', workflow_file_loc, '--parallel'])
		# assert result.exit_code == 0