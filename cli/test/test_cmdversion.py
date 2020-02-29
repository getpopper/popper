from click.testing import CliRunner
import popper.commands.cmd_version as version
import unittest
from popper_test import PopperTest


class TestCommandVersion(unittest.TestCase, PopperTest):

    def test_version(self):
        runner = CliRunner()
        result = runner.invoke(version.cli)
        assert result.exit_code == 0
