from click.testing import CliRunner
import unittest
from popper_test import PopperTest
import popper.commands.cmd_scaffold as scaffold
import unittest
import os
import subprocess
import sys


class TestScaffold(unittest.TestCase, PopperTest):

	def test_scaffold(self):

		runner = CliRunner()
		repo = self.mk_repo()
		#result = runner.invoke(scaffold.cli)

