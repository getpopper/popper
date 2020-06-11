import tempfile

from click.testing import CliRunner

import popper.commands.cmd_dot as dot

from popper.cli import log

from .test_common import PopperTest


class TestDot(PopperTest):
    def setUp(self):
        log.setLevel("CRITICAL")

    def test_dot(self):
        with tempfile.NamedTemporaryFile(mode="w+t", suffix=".yml") as f:
            f.write(
                """
steps:
- id: one
  uses: 'foo/bar'
- id: two
  uses: 'foo/bar'
- id: three
  uses: 'foo/bar'
"""
            )
            f.flush()

            runner = CliRunner()

            with self.assertLogs("popper") as test_logger:
                result = runner.invoke(dot.cli, ["-f", f.name])
                log.debug(f"file: {f.name}")
                self.assertEqual(result.exit_code, 0)
                log_output = test_logger.output[0]
                self.assertTrue('"one" -> "two";' in log_output)
                self.assertTrue('"two" -> "three";' in log_output)
                self.assertFalse("fillcolor=transparent,color=" in log_output)

            with self.assertLogs("popper") as test_logger:

                result = runner.invoke(dot.cli, ["--colors", "-f", f.name])
                self.assertEqual(result.exit_code, 0)
                self.assertTrue("fillcolor=transparent,color=" in test_logger.output[0])
