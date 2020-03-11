from click.testing import CliRunner
import unittest
from popper_test import PopperTest
import popper.commands.cmd_run as run
import unittest
import os
import subprocess
import sys


class TestSkip(unittest.TestCase, PopperTest):

    def test_skip(self):

        workflow_file_loc = self._wfile("skip", "workflow")

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
            run.cli, ['--wfile', workflow_file_loc, '--dry-run', '--skip',
                      'a1', '--skip', 'a2'])
        assert result.exit_code == 1

        result = self.check_output(['popper', 'run', '--dry-run', '--wfile',
                                    workflow_file_loc, '--skip', 'a1'],
                                   ["a2", "b", "c", "d"])
        assert result == 0

        result = self.check_output(
            ['popper', 'run', '--wfile', workflow_file_loc, '--dry-run',
             '--skip', 'a2'], ['a1', 'b', 'c', 'd'])
        assert result == 0

        result = runner.invoke(
            run.cli, ['--wfile', workflow_file_loc, '--dry-run',
                      '--skip', 'b', '--skip', 'c'])
        assert result.exit_code == 1

        result = self.check_output(
            ['popper', 'run', '--wfile', workflow_file_loc, '--dry-run',
             '--skip', 'b'], ['a1', 'a2', 'c', 'd'])
        assert result == 0

        result = self.check_output(
            ['popper', 'run', '--wfile', workflow_file_loc, '--dry-run',
             '--skip', 'c'], ['a1', 'a2', 'b', 'd'])
        assert result == 0

        result = self.check_output(
            ['popper', 'run', '--wfile', workflow_file_loc, '--dry-run',
             '--skip', 'd'], ['a1', 'a2', 'b', 'c'])
        assert result == 0

        workflow_file_loc = self._wfile("wrong", "yml")

        result = runner.invoke(
            run.cli, ['-f', workflow_file_loc, '--dry-run'])
        assert result.exit_code == 1
