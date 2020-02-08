from click.testing import CliRunner
import popper.commands.cmd_version as version
import popper.commands.cmd_run as run
import popper.utils as pu
from pathlib import Path
import unittest
import os
from popper.cli import log
import shutil


class TestCommandVersion(unittest.TestCase):

    def test_version(self):
        runner = CliRunner()
        result = runner.invoke(version.cli)
        assert result.exit_code == 0


class TestSkip(unittest.TestCase):

    def setUp(self):
        os.makedirs('/tmp/test_folder')
        os.chdir('/tmp/test_folder')
        log.setLevel('CRITICAL')

    def tearDown(self):
        os.chdir('/tmp')
        shutil.rmtree('/tmp/test_folder')
        log.setLevel('NOTSET')

    def create_workflow_file(self, content):
        f = open('/tmp/test_folder/a.workflow', 'w')
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

        runner = CliRunner()
        result = runner.invoke(
            run.cli, ['a1', '--wfile', '/tmp/test_folder/a.workflow',
                      '--skip', 'a2'])
        assert result.exit_code == 1

        result = runner.invoke(
            run.cli, ['--dry-run', '--wfile', '/tmp/test_folder/a.workflow',
                      'a1'])
        assert result.exit_code == 0

        result = runner.invoke(
            run.cli, ['--dry-run', '--wfile', '/tmp/test_folder/a.workflow',
                      'a1'])
        assert result.exit_code == 0

        result = runner.invoke(
            run.cli, ['--dry-run', '--wfile', '/tmp/test_folder/a.workflow',
                      'a2'])
        assert result.exit_code == 0

        result = runner.invoke(
            run.cli, ['--dry-run', '--wfile', '/tmp/test_folder/a.workflow',
                      'b'])
        assert result.exit_code == 0

        result = runner.invoke(
            run.cli, ['--dry-run', '--wfile', '/tmp/test_folder/a.workflow',
                      'c'])
        assert result.exit_code == 0

        result = runner.invoke(
            run.cli, ['--dry-run', '--wfile', '/tmp/test_folder/a.workflow',
                      'd'])
        assert result.exit_code == 0

        result = runner.invoke(
            run.cli, ['--dry-run', '--wfile', '/tmp/test_folder/a.workflow',
                      '--skip', 'e1'])
        assert result.exit_code == 1

        result = runner.invoke(
            run.cli, ['--dry-run', '--wfile', '/tmp/test_folder/a.workflow',
                      '--skip', 'a1', '--skip', 'a2'])
        assert result.exit_code == 1
