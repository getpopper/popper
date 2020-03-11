from click.testing import CliRunner
import unittest
from popper_test import PopperTest
import popper.commands.cmd_run as run
import unittest
import os
import subprocess
import sys


class TestSubstitutions(unittest.TestCase, PopperTest):

    def test_substitutions(self):

        workflow_file_loc = self._wfile("substitutions", "yml")
        runner = CliRunner()

        result = runner.invoke(run.cli, ['--dry-run', '-f', workflow_file_loc])
        assert result.exit_code == 1

        # This is used to set environment variable since on running the command
        # It will require value of the variable
        os.environ['TESTING'] = ''
        result = runner.invoke(run.cli, ['--dry-run', '-f', workflow_file_loc,
                                         '--substitution', '_VAR1=sh',
                                         '--substitution', '_VAR2=ls',
                                         '--substitution', '_VAR4=pwd',
                                         '--substitution', '_VAR5=TESTING',
                                         '--substitution', '_VAR6=TESTER',
                                         '--substitution', '_VAR7=TEST'])

        assert result.exit_code == 0

        result = runner.invoke(run.cli, ['--dry-run', '-f', workflow_file_loc,
                                         '--substitution', '_VAR1=shx',
                                         '--substitution', '_VAR2=ls',
                                         '--substitution', '_VAR4=pwd',
                                         '--substitution', '_VAR5=TESTING',
                                         '--substitution', '_VAR6=TESTER',
                                         '--substitution', '_VAR7=TEST'])

        assert result.exit_code == 1

        result = runner.invoke(run.cli, ['--dry-run', '-f', workflow_file_loc,
                                         '--substitution', '_VAR1=shx',
                                         '--substitution', '_VAR1=sh',
                                         '--substitution', '_VAR2=ls',
                                         '--substitution', '_VAR4=pwd',
                                         '--substitution', '_VAR5=TESTING',
                                         '--substitution', '_VAR6=TESTER',
                                         '--substitution', '_VAR7=TEST'])

        assert result.exit_code == 0

        result = runner.invoke(run.cli, ['--dry-run', '-f', workflow_file_loc,
                                         '--substitution', '_VAR1=shx',
                                         '--substitution', '_VAR1=sh',
                                         '--substitution', '_VAR2=ls',
                                         '--substitution', '_VAR4=pwd',
                                         '--substitution', '_VAR5=TESTING',
                                         '--substitution', '_VAR6=TESTER',
                                         '--substitution', '_VAR7=TEST',
                                         '--substitution', '_VAR8=EXTRA'])

        assert result.exit_code == 1

        result = runner.invoke(run.cli, ['--dry-run', '-f', workflow_file_loc,
                                         '--substitution', '_VAR1=shx',
                                         '--substitution', '_VAR1=sh',
                                         '--substitution', '_VAR2=ls',
                                         '--substitution', '_VAR4=pwd',
                                         '--substitution', '_VAR5=TESTING',
                                         '--substitution', '_VAR6=TESTER',
                                         '--substitution', '_VAR7=TEST',
                                         '--substitution', '_VAR8=EXTRA',
                                         '--allow-loose'])

        assert result.exit_code == 0

        result = runner.invoke(run.cli, ['--dry-run', '-f', workflow_file_loc,
                                         '--substitution', '_VAR1=shx',
                                         '--substitution', '_VAR1=sh',
                                         '--substitution', '_VAR2=ls',
                                         '--substitution', '_VAR4=pwd',
                                         '--substitution', '_VAR5=TESTING',
                                         '--substitution', '_VAR6=TESTER',
                                         '--substitution', '_VAR7=TEST',
                                         '--substitution', '_var8=EXTRA'])

        assert result.exit_code == 1

        result = runner.invoke(run.cli, ['--dry-run', '-f', workflow_file_loc,
                                         '--substitution', '_VAR1=shx',
                                         '--substitution', '_VAR1=sh',
                                         '--substitution', '_VAR2=ls',
                                         '--substitution', '_VAR4=pwd',
                                         '--substitution', '_VAR5=TESTING',
                                         '--substitution', '_VAR6=TESTER',
                                         '--substitution', '_VAR7=TEST',
                                         '--substitution', '_var8=EXTRA',
                                         '--allow-loose'])

        assert result.exit_code == 1
