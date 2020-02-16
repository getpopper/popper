from click.testing import CliRunner
import popper.commands.cmd_version as version
import popper.commands.cmd_run as run
import popper.utils as pu
from pathlib import Path
import unittest
import os
from popper.cli import log
import shutil
from test.test_common import *


class TestCommandVersion(unittest.TestCase):

    def test_version(self):
        runner = CliRunner()
        result = runner.invoke(version.cli)
        assert result.exit_code == 0


class TestSkip(unittest.TestCase):

    init_test_repo()
    os.chdir(os.environ.get('test_repo_path'))

    def create_workflow_file(self, content):
        f = open(os.environ.get('test_repo_path')+'/a.workflow', 'w+')
        f.write(content)
        f.close()

    def test_skip(self):

        self.create_workflow_file("""
        workflow "wf" {
          resolves = "d"
        }

        action "a1" {
          uses = "sh"
          args = "ls"
        }

        action "a2" {
          uses = "sh"
          args = "ls"
        }

        action "b" {
          needs = ["a1", "a2"]
          uses = "sh"
          args = "ls"
        }

        action "c" {
          needs = ["a1", "a2"]
          uses = "sh"
          args = "ls"
        }

        action "d" {
          needs = ["b", "c"]
          uses = "sh"
          args = "ls"
        }
        """)

        workflow_file_loc = os.environ.get('test_repo_path')+'/a.workflow'

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
