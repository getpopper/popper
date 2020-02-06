from click.testing import CliRunner
import popper.commands.cmd_ci as ci
import popper.commands.cmd_dot as dot
from pathlib import Path
import unittest


class TestCommands(unittest.TestCase):
	def test_ci(self):
		runner = CliRunner()
		result = runner.invoke(ci.cli, ['travis'])
		assert result.exit_code == 0

	def test_dot(self):
		runner = CliRunner()
		p = str(Path(__file__).parents[2])+'/ci/cli.workflow'
		result = runner.invoke(dot.cli,['--wfile',p])
		assert result.exit_code == 0