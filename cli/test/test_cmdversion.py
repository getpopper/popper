from click.testing import CliRunner

from popper import __version__
from popper.commands import cmd_version

from .test_common import PopperTest


class TestCommandVersion(PopperTest):

    def test_version(self):

        with self.assertLogs('popper') as test:
            runner = CliRunner()
            result = runner.invoke(cmd_version.cli)
            self.assertEqual(result.exit_code, 0)

        self.assertTrue(__version__ in test.output[0])
