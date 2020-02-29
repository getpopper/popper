from click.testing import CliRunner
import unittest
from popper_test import PopperTest
import popper.commands.cmd_run as run
import unittest


class TestSkip(unittest.TestCase, PopperTest):

    def test_skip(self):

        workflow_file_loc = 'cli/test/fixtures/skip.workflow'

        runner = CliRunner()
        result = runner.invoke(
            run.cli, ['a1', '--wfile', workflow_file_loc,
                      '--skip', 'a2'])
        assert result.exit_code == 1

        result = runner.invoke(
            run.cli, ['--dry-run', '--wfile', workflow_file_loc,
                      'a1'])
        assert result.exit_code == 0

        result = runner.invoke(
            run.cli, ['--dry-run', '--wfile', workflow_file_loc,
                      'a1'])
        assert result.exit_code == 0

        result = runner.invoke(
            run.cli, ['--dry-run', '--wfile', workflow_file_loc,
                      'a2'])
        assert result.exit_code == 0

        result = runner.invoke(
            run.cli, ['--dry-run', '--wfile', workflow_file_loc,
                      'b'])
        assert result.exit_code == 0

        result = runner.invoke(
            run.cli, ['--dry-run', '--wfile', workflow_file_loc,
                      'c'])
        assert result.exit_code == 0

        result = runner.invoke(
            run.cli, ['--dry-run', '--wfile', workflow_file_loc,
                      'd'])
        assert result.exit_code == 0

        result = runner.invoke(
            run.cli, ['--dry-run', '--wfile', workflow_file_loc,
                      '--skip', 'e1'])
        assert result.exit_code == 1

        result = runner.invoke(
            run.cli, ['--dry-run', '--wfile', workflow_file_loc,
                      '--skip', 'a1', '--skip', 'a2'])
        assert result.exit_code == 1
