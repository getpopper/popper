from click.testing import CliRunner
from popper.commands.cmd_ci import cli
import unittest


class TestCommandCi(unittest.TestCase):
    def test_ctx(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['travis'])
        assert result.exit_code == 0
