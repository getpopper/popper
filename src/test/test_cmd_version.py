from click.testing import CliRunner

from popper import __version__
from popper import _version_file
from popper.commands import cmd_version
from .test_common import PopperTest


class TestCommandVersion(PopperTest):
    def test_version(self):
        self.assertIsNot("0.0.0", __version__)
        with self.assertLogs("popper") as test:
            result = CliRunner().invoke(cmd_version.cli)
            self.assertTrue(__version__ in test.output[0])
            self.assertEqual(0, result.exit_code)

        with open(_version_file) as f:
            self.assertEqual(f"__popper_version__ = '{__version__}'\n", f.read())
