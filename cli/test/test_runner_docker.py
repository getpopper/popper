import os
import unittest

import utils as testutils

from popper.parser import YMLWorkflow
from popper.runner import WorkflowRunner

from popper.cli import log as log


class TestDockerRunner(unittest.TestCase):

    def setUp(self):
        log.setLevel('CRITICAL')

    @unittest.skipIf(os.environ['ENGINE'] != 'docker', 'ENGINE != docker')
    def test_basic_run(self):
        repo = testutils.mk_repo()

        with WorkflowRunner(workspace_dir=repo.working_dir) as r:
            wf = YMLWorkflow("""
            version: '1'
            steps:
            - uses: 'popperized/bin/sh@master'
              runs: [cat]
              args: README.md
            """)
            wf.parse()
            r.run(wf)

            wf = YMLWorkflow("""
            version: '1'
            steps:
            - uses: 'docker://alpine:3.9'
              runs: ['sh', '-c', 'echo $FOO > hello.txt ; pwd']
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
            - uses: 'docker://alpine:3.9'
              runs: 'nocommandisnamedlikethis'
            """)
            wf.parse()
            self.assertRaises(Exception, r.run, wf)

        repo.close()

    @unittest.skipIf(os.environ['ENGINE'] != 'docker', 'ENGINE != docker')
    def test_local_dockerfile(self):
        pass

    def test_skip_pull(self):
        pass
