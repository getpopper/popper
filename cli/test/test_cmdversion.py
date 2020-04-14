from click.testing import CliRunner
import popper.commands.cmd_version as version
import unittest
from popper_test import PopperTest
from popper import __version__ as version_value


class TestCommandVersion(unittest.TestCase, PopperTest):

    def test_version(self):

	    with self.assertLogs('popper') as test:
	        runner = CliRunner()
	        result = runner.invoke(version.cli)
	        assert result.exit_code == 0

	    if(version_value in test.output[0]):
	    	assert 1 == 1

	    else:
	    	assert 1 == 0