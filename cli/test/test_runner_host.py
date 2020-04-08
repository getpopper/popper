import os
import unittest

import utils as testutils

from popper.config import PopperConfig
from popper.parser import YMLWorkflow
from popper.runner import WorkflowRunner
from popper.runner_host import HostRunner

from popper.cli import log as log


class TestHostHostRunner(unittest.TestCase):
    def setUp(self):
        log.setLevel('CRITICAL')

    def test_run(self):
        repo = testutils.mk_repo()
        conf = PopperConfig(workspace_dir=repo.working_dir)

        with WorkflowRunner(conf) as r:
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

    def test_exec_cmd(self):
        cmd = ["echo", "command_1"]
        pid, ecode, output = HostRunner.exec_cmd(cmd, logging=False)
        self.assertGreater(pid, 0)
        self.assertEqual(ecode, 0)
        self.assertEqual(output, "command_1\n")

        pid, ecode, output = HostRunner.exec_cmd(cmd, logging=True)
        self.assertGreater(pid, 0)
        self.assertEqual(ecode, 0)
        self.assertEqual(output, "")

        cmd = ["env"]
        pid, ecode, output = HostRunner.exec_cmd(
            cmd, env={'TESTACION': 'test'}, cwd="/tmp", logging=False)
        self.assertGreater(pid, 0)
        self.assertEqual(ecode, 0)
        self.assertTrue('TESTACION' in output)


class TestHostDockerRunner(unittest.TestCase):
    def setUp(self):
        log.setLevel('CRITICAL')

    @unittest.skipIf(os.environ['ENGINE'] != 'docker', 'ENGINE != docker')
    def test_docker_basic_run(self):
        repo = testutils.mk_repo()
        conf = PopperConfig(workspace_dir=repo.working_dir)

        with WorkflowRunner(conf) as r:
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
