from click.testing import CliRunner
import unittest
from popper_test import PopperTest
import popper.commands.cmd_run as run
import os
import subprocess
import sys


class TestSkip(unittest.TestCase, PopperTest):

    def test_skip(self):

        workflow_file_loc = self._wfile("skip", "workflow")

        runner = CliRunner()
        with self.assertLogs('popper') as test:

          result = runner.invoke(
              run.cli, ['a1', '--wfile', workflow_file_loc,
                        '--skip', 'a2'])
          assert result.exit_code == 1

        self.assertListEqual(test.output,['ERROR:popper:`--skip` can not be used when STEP argument is passed.'])

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

        with self.assertLogs('popper') as test:

          result = runner.invoke(
              run.cli, ['--dry-run', '--wfile', workflow_file_loc,
                        '--skip', 'e1'])
          assert result.exit_code == 1

        #print("output : ", test.output)
        self.assertListEqual(test.output, ["ERROR:popper:Referenced step 'e1 missing."])
        
        with self.assertLogs('popper') as test:

          result = runner.invoke(
              run.cli, ['--wfile', workflow_file_loc, '--dry-run', '--skip',
                        'a1', '--skip', 'a2'])
          assert result.exit_code == 1

        if(all(x in test.output[0] for x in ['ERROR','Unreachable step(s):','d','b','c'])):
          assert 1 == 1

        else:
          assert 1 == 0

        with self.assertLogs('popper') as test:

          result = runner.invoke(run.cli,['--dry-run', '--wfile',
                                      workflow_file_loc, '--skip', 'a1'])
          assert result.exit_code == 0

        self.assertListEqual(test.output,["INFO:popper:[a2] ['ls']", "INFO:popper:Step 'a2' ran successfully !", "INFO:popper:[b] ['ls']", "INFO:popper:Step 'b' ran successfully !", "INFO:popper:[c] ['ls']", "INFO:popper:Step 'c' ran successfully !", "INFO:popper:[d] ['ls']", "INFO:popper:Step 'd' ran successfully !", 'INFO:popper:Workflow finished successfully.'])

        with self.assertLogs('popper') as test:

          result = runner.invoke(run.cli,['--wfile', workflow_file_loc, '--dry-run',
               '--skip', 'a2'])
          assert result.exit_code == 0

        self.assertListEqual(test.output, ["INFO:popper:[a1] ['ls']", "INFO:popper:Step 'a1' ran successfully !", "INFO:popper:[b] ['ls']", "INFO:popper:Step 'b' ran successfully !", "INFO:popper:[c] ['ls']", "INFO:popper:Step 'c' ran successfully !", "INFO:popper:[d] ['ls']", "INFO:popper:Step 'd' ran successfully !", 'INFO:popper:Workflow finished successfully.'])

        with self.assertLogs('popper') as test:

          result = runner.invoke(
              run.cli, ['--wfile', workflow_file_loc, '--dry-run',
                        '--skip', 'b', '--skip', 'c'])
          assert result.exit_code == 1

        self.assertListEqual(test.output, ['ERROR:popper:Unreachable step(s): d.'])

        with self.assertLogs('popper') as test:

          result = runner.invoke(run.cli, ['--wfile', workflow_file_loc, '--dry-run',
               '--skip', 'b'])
          assert result.exit_code == 0

        self.assertListEqual(test.output, ["INFO:popper:[a1] ['ls']", "INFO:popper:Step 'a1' ran successfully !", "INFO:popper:[a2] ['ls']", "INFO:popper:Step 'a2' ran successfully !", "INFO:popper:[c] ['ls']", "INFO:popper:Step 'c' ran successfully !", "INFO:popper:[d] ['ls']", "INFO:popper:Step 'd' ran successfully !", 'INFO:popper:Workflow finished successfully.'])

        with self.assertLogs('popper') as test:

          result = runner.invoke(run.cli, ['--wfile', workflow_file_loc, '--dry-run',
               '--skip', 'c'])
          assert result.exit_code == 0

        self.assertListEqual(test.output, ["INFO:popper:[a1] ['ls']", "INFO:popper:Step 'a1' ran successfully !", "INFO:popper:[a2] ['ls']", "INFO:popper:Step 'a2' ran successfully !", "INFO:popper:[b] ['ls']", "INFO:popper:Step 'b' ran successfully !", "INFO:popper:[d] ['ls']", "INFO:popper:Step 'd' ran successfully !", 'INFO:popper:Workflow finished successfully.'])
        
        with self.assertLogs('popper') as test:

          result = runner.invoke(run.cli,
              ['--wfile', workflow_file_loc, '--dry-run',
               '--skip', 'd'])
          assert result.exit_code == 0

        self.assertListEqual(test.output, ["INFO:popper:[a1] ['ls']", "INFO:popper:Step 'a1' ran successfully !", "INFO:popper:[a2] ['ls']", "INFO:popper:Step 'a2' ran successfully !", "INFO:popper:[b] ['ls']", "INFO:popper:Step 'b' ran successfully !", "INFO:popper:[c] ['ls']", "INFO:popper:Step 'c' ran successfully !", 'INFO:popper:Workflow finished successfully.'])

        workflow_file_loc = self._wfile("wrong", "yml")

        with self.assertLogs('popper') as test:

          result = runner.invoke(
              run.cli, ['-f', workflow_file_loc, '--dry-run'])
          assert result.exit_code == 1

        self.assertListEqual(test.output, ["ERROR:popper:Step 'wrong' referenced in workflow but missing"])
