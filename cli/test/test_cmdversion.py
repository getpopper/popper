from click.testing import CliRunner
import popper.commands.cmd_version as version
import unittest
from test_common import PopperTest
from popper import __version__ as version_value


class TestCommandVersion(PopperTest):

    def test_version(self):

        with self.assertLogs('popper') as test:
            runner = CliRunner()
            result = runner.invoke(version.cli)
            self.assertEqual(result.exit_code, 0)

        self.assertTrue(version_value in test.output[0])
