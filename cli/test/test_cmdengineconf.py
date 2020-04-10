from click.testing import CliRunner
import unittest
from popper_test import PopperTest
import popper.commands.cmd_run as run
import os
import subprocess
import sys


class TestEngineConf(unittest.TestCase, PopperTest):

    def test_eng_conf(self):

    	workflow_file_loc = self._wfile("engine-conf", "yml")
    	runner = CliRunner()

    	with self.assertLogs("popper") as test:
    		result = runner.invoke(run.cli,['--wfile', workflow_file_loc])
    		assert result.exit_code == 0

    	print(test.output)

    	with self.assertLogs("popper") as test:

    		settings_file = os.getcwd()+'/cli/test/fixtures/settings.yml'
    		result = runner.invoke(run.cli, ['--wfile', workflow_file_loc, '--conf', settings_file])
    		assert result.exit_code == 0

    	print(test.output)