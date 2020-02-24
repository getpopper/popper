import os
import unittest

from . import utils as testutils

from popper.parser import YMLWorkflow
from popper.runner import WorkflowRunner

from popper.cli import log as log


class TestHostRunner(unittest.TestCase):
    def setUp(self):
        log.setLevel('DEBUG')

    def test_run(self):
        repo = testutils.mk_repo()
        currdir = os.getcwd()
        os.chdir(repo.working_dir)

        with WorkflowRunner() as r:
            wf = YMLWorkflow("""
            version: '1'
            steps:
            - uses: sh
              runs: [cat]
              args: README.md
            """)
            wf.parse()
            r.run(wf)

            wf = YMLWorkflow("""
            version: '1'
            steps:
            - uses: 'sh'
              runs: ['bash', '-c', 'echo $FOO > hello.txt ; pwd']
              env: {
                  FOO: bar
              }
            """)
            wf.parse()
            r.run(wf)
            with open(os.path.join(repo.working_dir, 'hello.txt'), 'r') as f:
                self.assertEqual(f.read(), 'bar\n')

            wf = YMLWorkflow("""
            version: '1'
            steps:
            - uses: 'sh'
              runs: 'nocommandisnamedlikethis'
            """)
            wf.parse()
            self.assertRaises(SystemExit, r.run, wf)

        repo.close()
        os.chdir(currdir)