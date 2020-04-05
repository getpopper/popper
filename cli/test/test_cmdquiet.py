from click.testing import CliRunner
import unittest
from popper_test import PopperTest
import popper.commands.cmd_run as run
import unittest
import os
import subprocess
import sys

class TestQuiet(unittest.TestCase, PopperTest):

    def test_quiet(self):

    	workflow_file_loc = self._wfile("quiet", "yml")
    	runner = CliRunner()

    	with self.assertLogs('popper') as test:
    		result = runner.invoke(run.cli, ['--wfile', workflow_file_loc])
    		assert result.exit_code == 0

    	output_without_quiet = test.output


    	with self.assertLogs('popper') as test:

    		result = runner.invoke(run.cli, ['--wfile', workflow_file_loc, '--quiet'])
    		assert result.exit_code == 0

    	output_with_quiet = test.output

    	if(len(output_with_quiet) < len(output_without_quiet)):

    		assert 0 == 0

    	else:

    		assert 1 == 0






