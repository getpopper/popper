import os
import unittest
import shutil

from dotmap import DotMap
from unittest.mock import patch
from popper.parser import YMLWorkflow
from popper.runner import WorkflowRunner, StepRunner

from popper.cli import log


class TestWorkflowRunner(unittest.TestCase):
    def setUp(self):
        log.setLevel('CRITICAL')

    def test_check_secrets(self):
        wf = YMLWorkflow("""
        version: '1'
        steps:
        - uses: docker://alpine:3.9
          args: ["ls -ltr"]
          secrets: ["SECRET_ONE", "SECRET_TWO"]
        """)
        wf.parse()

        # in dry-run, secrets are ignored
        WorkflowRunner.process_secrets(wf, DotMap({'dry_run': True}))

        # when CI=true it should fail
        os.environ['CI'] = 'true'
        self.assertRaises(SystemExit, WorkflowRunner.process_secrets, wf)

        # add one secret
        os.environ['SECRET_ONE'] = '1234'

        # it should fail again, as we're missing one
        self.assertRaises(SystemExit, WorkflowRunner.process_secrets, wf)

        os.environ.pop('CI')

        # now is fine
        with patch('getpass.getpass', return_value='5678'):
            WorkflowRunner.process_secrets(wf)

        # pop the other
        os.environ.pop('SECRET_ONE')

    def test_clone_repos(self):
        wf = YMLWorkflow("""
        version: '1'
        steps:
        - uses: popperized/bin/sh@master
        """)
        wf.parse()

        wid = '12345'
        cache_dir = os.path.join(os.environ['HOME'], '.cache/popper/')

        # clone repos in the default cache directory.
        WorkflowRunner.clone_repos(wf, DotMap({'wid': wid}))
        self.assertTrue(
            os.path.exists(
                os.path.join(cache_dir, wid, 'github.com/popperized/bin')))

        # clone repos in custom cache directory
        os.environ['POPPER_CACHE_DIR'] = '/tmp/smdir'
        WorkflowRunner.clone_repos(wf, DotMap({'wid': wid}))
        self.assertTrue(
            os.path.exists(
                os.path.join('/tmp/smdir', wid, 'github.com/popperized/bin')))
        os.environ.pop('POPPER_CACHE_DIR')

        # check failure when container is not available and we skip cloning
        shutil.rmtree('/tmp/smdir')
        shutil.rmtree(cache_dir)
        self.assertRaises(SystemExit, WorkflowRunner.clone_repos, wf,
                          DotMap({'wid': wid, 'skip_clone': True}))

    def test_steprunner_factory(self):
        with WorkflowRunner() as r:
            self.assertEqual(r.get_step_runner('host').__class__.__name__,
                             'HostRunner')
            self.assertEqual(r.get_step_runner('docker').__class__.__name__,
                             'DockerRunner')


class TestStepRunner(unittest.TestCase):
    def setUp(self):
        log.setLevel('CRITICAL')

    def test_prepare_environment(self):
        step = {'name': 'a', 'env': {'FOO': 'BAR'}, 'secrets': ['A']}
        os.environ['A'] = 'BC'
        env = StepRunner.prepare_environment(step, {'another': 'b'})
        self.assertDictEqual(env, {'FOO': 'BAR', 'A': 'BC', 'another': 'b'})
        os.environ.pop('A')
