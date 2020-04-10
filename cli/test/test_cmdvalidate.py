from click.testing import CliRunner
import unittest
from popper_test import PopperTest
import popper.commands.cmd_run as run
import unittest
import os
import subprocess
import sys


class TestValidate(unittest.TestCase, PopperTest):

    def test_validate(self):

        workflow_file_loc = self._wfile("validate-wf1", "workflow")
        runner = CliRunner()

        with self.assertLogs('popper') as test:

            result = runner.invoke(
                run.cli, ['--dry-run', '--wfile', workflow_file_loc])
            assert result.exit_code == 1

        self.assertListEqual(
            test.output, ['ERROR:popper:Cannot have more than one workflow blocks.'])

        with self.assertLogs('popper') as test:

            workflow_file_loc = self._wfile("validate-wf2", "workflow")
            result = runner.invoke(
                run.cli, ['--dry-run', '--wfile', workflow_file_loc])
            assert result.exit_code == 1

        self.assertListEqual(
            test.output, ["ERROR:popper:Invalid workflow attribute 'attr1'."])

        with self.assertLogs('popper') as test:

            workflow_file_loc = self._wfile("validate-wf3", "workflow")
            result = runner.invoke(
                run.cli, ['--dry-run', '--wfile', workflow_file_loc])
            assert result.exit_code == 1

        self.assertListEqual(
            test.output, ['ERROR:popper:A workflow block must be present.'])

        workflow_file_loc = self._wfile("validate-wf4", "workflow")
        result = runner.invoke(run.cli, ['--dry-run', '--wfile', workflow_file_loc])
        assert result.exit_code == 0

        with self.assertLogs('popper') as test:
            workflow_file_loc = self._wfile("validate-wf5", "workflow")
            result = runner.invoke(
                run.cli, ['--dry-run', '--wfile', workflow_file_loc])
            assert result.exit_code == 1

        self.assertListEqual(
            test.output, ["ERROR:popper:Invalid workflow attribute 'foo'."])

        with self.assertLogs('popper') as test:

            workflow_file_loc = self._wfile("validate-wf6", "workflow")
            result = runner.invoke(
                run.cli, ['--dry-run', '--wfile', workflow_file_loc])
            assert result.exit_code == 1

        self.assertListEqual(test.output, [
                             'ERROR:popper:[resolves] attribute must be a string or a list of strings.'])

        workflow_file_loc = self._wfile("validate-wf7", "workflow")
        result = runner.invoke(
            run.cli, ['--dry-run', '--wfile', workflow_file_loc])
        assert result.exit_code == 0

        with self.assertLogs('popper') as test:

            workflow_file_loc = self._wfile("validate-wf8", "workflow")
            result = runner.invoke(
                run.cli, ['--dry-run', '--wfile', workflow_file_loc])
            assert result.exit_code == 1

        self.assertListEqual(
            test.output, ['ERROR:popper:[on] attribute mist be a string.'])

        workflow_file_loc = self._wfile("validate-wf9", "workflow")
        result = runner.invoke(
            run.cli, ['--dry-run', '--wfile', workflow_file_loc])
        assert result.exit_code == 0

        with self.assertLogs('popper') as test:

            workflow_file_loc = self._wfile("validate-wf10", "workflow")
            result = runner.invoke(
                run.cli, ['--dry-run', '--wfile', workflow_file_loc])
            assert result.exit_code == 1

        self.assertListEqual(
            test.output, ["ERROR:popper:Invalid step attribute 'attr1'."])

        with self.assertLogs('popper') as test:

            workflow_file_loc = self._wfile("validate-wf11", "workflow")
            result = runner.invoke(
                run.cli, ['--dry-run', '--wfile', workflow_file_loc])
            assert result.exit_code == 1

        self.assertListEqual(
            test.output, ['ERROR:popper:At least one step block must be present.'])

        workflow_file_loc = self._wfile("validate-wf12", "workflow")
        result = runner.invoke(
            run.cli, ['--dry-run', '--wfile', workflow_file_loc])
        assert result.exit_code == 0

        with self.assertLogs('popper') as test:

            workflow_file_loc = self._wfile("validate-wf13", "workflow")
            result = runner.invoke(
                run.cli, ['--dry-run', '--wfile', workflow_file_loc])
            assert result.exit_code == 1

        self.assertListEqual(
            test.output, ['ERROR:popper:[uses] attribute must be present in step block.'])

        with self.assertLogs('popper') as test:

            workflow_file_loc = self._wfile("validate-wf14", "workflow")
            result = runner.invoke(
                run.cli, ['--dry-run', '--wfile', workflow_file_loc])
            assert result.exit_code == 1

        self.assertListEqual(
            test.output, ['ERROR:popper:[uses] attribute must be a string.'])

        workflow_file_loc = self._wfile("validate-wf15", "workflow")
        result = runner.invoke(
            run.cli, ['--dry-run', '--wfile', workflow_file_loc])
        assert result.exit_code == 0

        with self.assertLogs('popper') as test:

            workflow_file_loc = self._wfile("validate-wf16", "workflow")
            result = runner.invoke(
                run.cli, ['--dry-run', '--wfile', workflow_file_loc])
            assert result.exit_code == 1

        self.assertListEqual(test.output, [
                             'ERROR:popper:[needs] attribute must be a string or a list of strings.'])

        workflow_file_loc = self._wfile("validate-wf17", "workflow")
        result = runner.invoke(
            run.cli, ['--dry-run', '--wfile', workflow_file_loc])
        assert result.exit_code == 0

        with self.assertLogs('popper') as test:

            workflow_file_loc = self._wfile("validate-wf18", "workflow")
            result = runner.invoke(
                run.cli, ['--dry-run', '--wfile', workflow_file_loc])
            assert result.exit_code == 1

        self.assertListEqual(test.output, [
                             'ERROR:popper:[runs] attribute must be a string or a list of strings.'])

        workflow_file_loc = self._wfile("validate-wf19", "workflow")
        result = runner.invoke(
            run.cli, ['--dry-run', '--wfile', workflow_file_loc])
        assert result.exit_code == 0

        with self.assertLogs('popper') as test:

            workflow_file_loc = self._wfile("validate-wf20", "workflow")
            result = runner.invoke(
                run.cli, ['--dry-run', '--wfile', workflow_file_loc])
            assert result.exit_code == 1

        self.assertListEqual(test.output, [
                             'ERROR:popper:[args] attribute must be a string or a list of strings.'])

        workflow_file_loc = self._wfile("validate-wf21", "workflow")
        result = runner.invoke(
            run.cli, ['--dry-run', '--wfile', workflow_file_loc])
        assert result.exit_code == 0

        with self.assertLogs('popper') as test:

            workflow_file_loc = self._wfile("validate-wf22", "workflow")
            result = runner.invoke(
                run.cli, ['--dry-run', '--wfile', workflow_file_loc])
            assert result.exit_code == 1

        self.assertListEqual(
            test.output, ['ERROR:popper:[env] attribute must be a dict.'])

        workflow_file_loc = self._wfile("validate-wf23", "workflow")
        result = runner.invoke(
            run.cli, ['--dry-run', '--wfile', workflow_file_loc])
        assert result.exit_code == 0

        with self.assertLogs('popper') as test:

            workflow_file_loc = self._wfile("validate-wf24", "workflow")
            result = runner.invoke(
                run.cli, ['--dry-run', '--wfile', workflow_file_loc])
            assert result.exit_code == 1

        self.assertListEqual(test.output, [
                             'ERROR:popper:[secrets] attribute must be a string or a list of strings.'])

        os.environ['F_NAME'] = 'F_NAME'
        os.environ['L_NAME'] = 'L_NAME'

        workflow_file_loc = self._wfile("validate-wf25", "workflow")
        result = runner.invoke(
            run.cli, ['--dry-run', '--wfile', workflow_file_loc])
        assert result.exit_code == 0
