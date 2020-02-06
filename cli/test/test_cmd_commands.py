from click.testing import CliRunner
import popper.commands.cmd_ci as ci
import popper.commands.cmd_dot as dot
import popper.commands.cmd_info as info
import popper.commands.cmd_run as run
import popper.commands.cmd_scaffold as scaffold
import popper.commands.cmd_search as search
import popper.commands.cmd_version as version
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
        result = runner.invoke(dot.cli, ['--wfile', p])
        assert result.exit_code == 0

    def test_run(self):
        runner = CliRunner()
        p = str(Path(__file__).parents[2])+'/ci/cli.workflow'
        result = runner.invoke(run.cli, ['--wfile', p])
        print(result)
        assert result.exit_code == 0

    def test_info(self):
        runner = CliRunner()
        result = runner.invoke(info.cli, ['popperized/npm'])
        assert result.exit_code == 0

    def test_scaffold(self):
        runner = CliRunner()
        result = runner.invoke(scaffold.cli)
        assert result.exit_code == 0

    def test_search(self):
        runner = CliRunner()
        result = runner.invoke(search.cli, ['popperized/npm'])
        assert result.exit_code == 0

    def test_version(self):
        runner = CliRunner()
        result = runner.invoke(version.cli)
        assert result.exit_code == 0
