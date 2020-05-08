import tempfile
import git

from click.testing import CliRunner

import popper.commands.cmd_dot as dot

from .test_common import PopperTest


class TestDot(PopperTest):
    def test_dot(self):

        wf_dir = tempfile.mkdtemp()
        runner = CliRunner()
        git.Git(wf_dir).clone("https://github.com/popperized/github-actions-demo.git")

        workflow_path = f"{wf_dir}/github-actions-demo/.github/main.workflow"

        with self.assertLogs("popper") as test_logger:

            result = runner.invoke(dot.cli, ["-f", workflow_path])
            self.assertEqual(result.exit_code, 0)
            log_output = test_logger.output[0]
            self.assertTrue('"branch-filter" -> "deploy";' in log_output)
            self.assertTrue('"install" -> "lint";' in log_output)
            self.assertTrue('"install" -> "test";' in log_output)
            self.assertTrue('"lint" -> "branch-filter";' in log_output)
            self.assertTrue('"test-and-deploy" -> "install";' in log_output)
            self.assertTrue('"test" -> "branch-filter"' in log_output)
            self.assertFalse("fillcolor=transparent,color=" in log_output)

        with self.assertLogs("popper") as test_logger:

            result = runner.invoke(dot.cli, ["--colors", "-f", workflow_path])
            self.assertEqual(result.exit_code, 0)
            self.assertTrue("fillcolor=transparent,color=" in test_logger.output[0])
