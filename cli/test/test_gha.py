import os
import signal
import shutil
import unittest
try:
    from unittest.mock import patch
except ImportError:
    from mock import patch
import multiprocessing as mp

import docker
import git

from popper.cli import log
from popper.parser import Workflow
from popper.gha import (WorkflowRunner,
                        ActionRunner,
                        DockerRunner,
                        SingularityRunner,
                        HostRunner)
import popper.utils as pu
from concurrent.futures import ThreadPoolExecutor, as_completed


class TestWorkflowRunner(unittest.TestCase):

    def setUp(self):
        os.makedirs('/tmp/test_folder')
        os.chdir('/tmp/test_folder')
        log.setLevel('CRITICAL')

    def tearDown(self):
        os.chdir('/tmp')
        shutil.rmtree('/tmp/test_folder')
        log.setLevel('NOTSET')

    def test_check_secrets(self):
        os.environ['SECRET_ONE'] = '1234'
        os.environ['SECRET_TWO'] = '5678'
        pu.write_file('/tmp/test_folder/a.workflow', """
        workflow "sample" {
            resolves = "a"
        }

        action "a" {
            uses = "popperized/bin/sh@master"
            args = ["ls -ltr"]
            secrets = ["SECRET_ONE", "SECRET_TWO"]
        }
        """)
        wf = Workflow('/tmp/test_folder/a.workflow')
        wf.parse()
        WorkflowRunner.check_secrets(wf, False, False)
        WorkflowRunner.check_secrets(wf, True, False)
        WorkflowRunner.check_secrets(wf, False, True)

        os.environ.pop('SECRET_ONE')
        pu.write_file('/tmp/test_folder/a.workflow', """
        workflow "sample" {
            resolves = "a"
        }

        action "a" {
            uses = "popperized/bin/sh@master"
            args = ["ls -ltr"]
            secrets = ["SECRET_ONE", "SECRET_TWO"]
        }
        """)
        wf = Workflow('/tmp/test_folder/a.workflow')
        wf.parse()
        os.environ['CI'] = 'false'
        with patch('getpass.getpass', return_value='1234') as fake_input:
            WorkflowRunner.check_secrets(wf, False, False)

        os.environ['CI'] = 'true'
        os.environ.pop('SECRET_ONE')
        self.assertRaises(
            SystemExit,
            WorkflowRunner.check_secrets,
            wf,
            False,
            False)

    def test_instantiate_runners(self):
        pu.write_file('/tmp/test_folder/a.workflow', """
        workflow "sample" {
            resolves = "a"
        }

        action "a" {
            uses = "sh"
            args = "ls"
        }
        """)
        wf = Workflow('/tmp/test_folder/a.workflow')
        wf.parse()
        env = WorkflowRunner.get_workflow_env(wf, '/tmp/test_folder')
        WorkflowRunner.instantiate_runners(
            'docker', wf, '/tmp/test_folder', False, False, '12345')
        self.assertIsInstance(wf.action['a']['runner'], HostRunner)

        os.makedirs('/tmp/test_folder/actions/sample')
        pu.write_file('/tmp/test_folder/actions/sample/entrypoint.sh')
        pu.write_file('/tmp/test_folder/actions/sample/README.md')

        pu.write_file('/tmp/test_folder/a.workflow', """
        workflow "sample" {
            resolves = "a"
        }

        action "a" {
            uses = "./actions/sample"

        }
        """)
        wf = Workflow('/tmp/test_folder/a.workflow')
        wf.parse()
        env = WorkflowRunner.get_workflow_env(wf, '/tmp/test_folder')
        WorkflowRunner.instantiate_runners(
            'singularity', wf, '/tmp/test_folder', False, False, '12345')
        self.assertIsInstance(wf.action['a']['runner'], HostRunner)

        pu.write_file('/tmp/test_folder/a.workflow', """
        workflow "sample" {
            resolves = "a"
        }

        action "a" {
            uses = "popperized/bin/sh@master"
        }
        """)
        wf = Workflow('/tmp/test_folder/a.workflow')
        wf.parse()
        env = WorkflowRunner.get_workflow_env(wf, '/tmp/test_folder')
        WorkflowRunner.instantiate_runners(
            'singularity', wf, '/tmp/test_folder', False, False, '12345')
        self.assertIsInstance(wf.action['a']['runner'], SingularityRunner)

        WorkflowRunner.instantiate_runners(
            'docker', wf, '/tmp/test_folder', False, False, '12345')
        self.assertIsInstance(wf.action['a']['runner'], DockerRunner)

    def test_download_actions(self):
        pu.write_file('/tmp/test_folder/a.workflow', """
        workflow "sample" {
            resolves = "a"
        }

        action "a" {
            uses = "popperized/bin/sh@master"
        }

        action "b" {
            uses = "popperized/ansible@master"
        }
        """)
        wf = Workflow('/tmp/test_folder/a.workflow')
        wf.parse()

        # Download actions in the default cache directory.
        WorkflowRunner.download_actions(wf, False, False, '12345')
        self.assertEqual(
            os.path.exists(
                os.environ['HOME'] +
                '/.cache/.popper/actions/12345/github.com'),
            True)

        # Download actions in custom cache directory
        os.environ['POPPER_CACHE_DIR'] = '/tmp/somedir'
        WorkflowRunner.download_actions(wf, False, False, '12345')
        self.assertEqual(os.path.exists(
            '/tmp/somedir/actions/12345/github.com'), True)
        os.environ.pop('POPPER_CACHE_DIR')

        # Release resources.
        shutil.rmtree('/tmp/somedir')
        shutil.rmtree(
            os.environ['HOME'] +
            '/.cache/.popper/actions/12345/github.com')

        # Test with skipclone flag when action not present in cache.
        self.assertRaises(
            SystemExit,
            WorkflowRunner.download_actions,
            wf,
            False,
            True,
            '12345')

    def test_get_workflow_env(self):
        pu.write_file('/tmp/test_folder/a.workflow', """
        workflow "sample" {
            resolves = "a"
        }

        action "a" {
            uses = "sh"
        }
        """)
        wf = Workflow('/tmp/test_folder/a.workflow')
        wf.parse()
        env = WorkflowRunner.get_workflow_env(wf, '/tmp/test_folder')
        self.assertDictEqual(env, {
            'HOME': os.environ['HOME'],
            'GITHUB_WORKFLOW': 'sample',
            'GITHUB_ACTION': '',
            'GITHUB_ACTOR': 'popper',
            'GITHUB_REPOSITORY': 'unknown',
            'GITHUB_EVENT_NAME': 'push',
            'GITHUB_EVENT_PATH': '/tmp/github_event.json',
            'GITHUB_WORKSPACE': '/tmp/test_folder',
            'GITHUB_SHA': 'unknown',
            'GITHUB_REF': 'unknown',
            'POPPER_WORKFLOW': 'sample',
            'POPPER_ACTION': '',
            'POPPER_ACTOR': 'popper',
            'POPPER_REPOSITORY': 'unknown',
            'POPPER_EVENT_NAME': 'push',
            'POPPER_EVENT_PATH': '/tmp/github_event.json',
            'POPPER_WORKSPACE': '/tmp/test_folder',
            'POPPER_SHA': 'unknown',
            'POPPER_REF': 'unknown'})


class TestActionRunner(unittest.TestCase):

    def setUp(self):
        os.makedirs('/tmp/test_folder')
        os.chdir('/tmp/test_folder')
        log.setLevel('CRITICAL')
        workflow = """
        workflow "sample" {
            resolves = "sample action"
        }

        action "sample action" {
            uses = "popperized/bin/sh@master"
            args = ["echo", "Hello"]
        }
        """
        pu.write_file('/tmp/test_folder/a.workflow', workflow)
        self.wf = Workflow('/tmp/test_folder/a.workflow')
        self.wf.parse()
        WorkflowRunner.instantiate_runners(
            'docker', self.wf, '/tmp/test_folder', False, False, '12345')
        self.runner = self.wf.action['sample action']['runner']

    def tearDown(self):
        os.chdir('/tmp')
        shutil.rmtree('/tmp/test_folder')
        log.setLevel('NOTSET')

    def test_check_executable(self):
        self.assertRaises(SystemExit,
                          self.runner.check_executable,
                          'abcd')

    def test_handle_exit(self):
        self.flag = 0

        def signal_handler(sig, frame):
            self.flag = 1

        signal.signal(signal.SIGUSR1, signal_handler)
        self.assertRaises(SystemExit, self.runner.handle_exit, 1)
        self.runner.handle_exit(0)
        self.assertEqual(self.flag, 0)
        self.runner.handle_exit(78)
        self.assertEqual(self.flag, 1)

    def test_prepare_environment(self):
        env = self.runner.prepare_environment()
        self.assertDictEqual(env, {
            'HOME': os.environ['HOME'],
            'GITHUB_WORKFLOW': 'sample',
            'GITHUB_ACTION': 'sample action',
            'GITHUB_ACTOR': 'popper',
            'GITHUB_REPOSITORY': 'unknown',
            'GITHUB_EVENT_NAME': 'push',
            'GITHUB_EVENT_PATH': '/tmp/github_event.json',
            'GITHUB_WORKSPACE': '/tmp/test_folder',
            'GITHUB_SHA': 'unknown', 'GITHUB_REF':
            'unknown', 'POPPER_WORKFLOW': 'sample',
            'POPPER_ACTION': 'sample action',
            'POPPER_ACTOR': 'popper',
            'POPPER_REPOSITORY': 'unknown',
            'POPPER_EVENT_NAME': 'push',
            'POPPER_EVENT_PATH': '/tmp/github_event.json',
            'POPPER_WORKSPACE': '/tmp/test_folder',
            'POPPER_SHA': 'unknown',
            'POPPER_REF': 'unknown'})

        self.assertEqual(set(env.keys()).issubset(set(os.environ)), False)
        env = self.runner.prepare_environment(set_env=True)
        self.assertEqual(set(env.keys()).issubset(set(os.environ)), True)
        self.runner.remove_environment()

    def test_remove_environment(self):
        env = self.runner.prepare_environment(set_env=True)
        self.assertEqual(set(env.keys()).issubset(set(os.environ)), True)
        self.runner.remove_environment()
        self.assertEqual(set(env.keys()).issubset(set(os.environ)), False)

    def test_setup_necessary_files(self):
        os.remove('/tmp/github_event.json')
        self.assertEqual(os.path.exists('/tmp/github_event.json'), False)
        self.runner.setup_necessary_files()
        self.assertEqual(os.path.exists('/tmp/github_event.json'), True)
        self.runner.workspace = '/tmp/a/b/c'
        self.runner.setup_necessary_files()
        self.assertEqual(os.path.exists('/tmp/a/b/c'), True)


class TestDockerRunner(unittest.TestCase):

    def setUp(self):
        os.makedirs('/tmp/test_folder')
        os.chdir('/tmp/test_folder')
        log.setLevel('CRITICAL')
        workflow = """
        workflow "sample" {
            resolves = "sample action"
        }

        action "sample action" {
            uses = "popperized/bin/sh@master"
            args = ["echo", "Hello"]
        }
        """
        pu.write_file('/tmp/test_folder/a.workflow', workflow)
        self.wf = Workflow('/tmp/test_folder/a.workflow')
        self.wf.parse()
        WorkflowRunner.download_actions(self.wf, False, False, '12345')
        WorkflowRunner.instantiate_runners(
            'docker', self.wf, '/tmp/test_folder', False, False, '12345')
        self.docker_client = docker.from_env()
        self.runner = self.wf.action['sample action']['runner']

    def tearDown(self):
        os.chdir('/tmp')
        shutil.rmtree('/tmp/test_folder')
        shutil.rmtree(os.path.join(os.environ['HOME'], '.cache/.popper'))
        log.setLevel('NOTSET')
        self.docker_client.close()

    @unittest.skipIf(
        os.environ['RUNTIME'] != 'docker',
        'Skipping docker tests...')
    def test_get_build_resources(self):
        res = self.runner.get_build_resources()
        self.assertTupleEqual(
            res,
            (True,
             'popperized/bin:master',
             os.environ['HOME'] +
             '/.cache/.popper/actions/12345/github.com/popperized/bin/sh'))
        self.runner.action['uses'] = 'docker://debian:buster-slim'
        res = self.runner.get_build_resources()
        self.assertTupleEqual(res,
                              (False, 'debian:buster-slim', None))
        self.runner.action['uses'] = './actions/jshint'
        res = self.runner.get_build_resources()
        self.assertTupleEqual(
            res, (True, 'jshint:unknown', '/tmp/test_folder/./actions/jshint'))

    @unittest.skipIf(
        os.environ['RUNTIME'] != 'docker',
        'Skipping docker tests...')
    def test_docker_exists(self):
        image = self.docker_client.images.pull('debian:buster-slim')
        container = self.docker_client.containers.create(
            image='debian:buster-slim',
            name='popper_sample_action_12345')
        self.assertEqual(self.runner.docker_exists(), True)
        container.remove()
        self.docker_client.images.remove('debian:buster-slim')

    @unittest.skipIf(
        os.environ['RUNTIME'] != 'docker',
        'Skipping docker tests...')
    def test_docker_image_exists(self):
        image = self.docker_client.images.pull('debian:buster-slim')
        self.assertEqual(self.runner.docker_image_exists(
            'debian:buster-slim'), True)
        self.docker_client.images.remove('debian:buster-slim', force=True)

    @unittest.skipIf(
        os.environ['RUNTIME'] != 'docker',
        'Skipping docker tests...')
    def test_docker_rm(self):
        self.docker_client.images.pull('debian:buster-slim')
        self.runner.docker_create('debian:buster-slim')
        self.runner.docker_rm()
        self.assertRaises(docker.errors.NotFound, self.runner.docker_rm)

    @unittest.skipIf(
        os.environ['RUNTIME'] != 'docker',
        'Skipping docker tests...')
    def test_docker_pull(self):
        self.assertEqual(self.runner.docker_image_exists(
            'debian:buster-slim'), False)
        self.runner.skip_pull = True
        self.assertRaises(
            SystemExit,
            self.runner.docker_pull,
            'debian:buster-slim')
        self.runner.skip_pull = False
        self.runner.docker_pull('debian:buster-slim')
        self.assertEqual(self.runner.docker_image_exists(
            'debian:buster-slim'), True)

    @unittest.skipIf(
        os.environ['RUNTIME'] != 'docker',
        'Skipping docker tests...')
    def test_docker_start(self):
        self.runner.action['runs'] = [
            "sh", "-c", "echo 'Hello from Popper 2.x !' > popper.file"
        ]
        self.runner.docker_pull('debian:buster-slim')
        self.runner.docker_create('debian:buster-slim')
        e = self.runner.docker_start()
        self.assertEqual(e, 0)
        self.assertEqual(os.path.exists('popper.file'), True)
        res = self.docker_client.containers.list(filters={'status': 'running'})
        self.assertListEqual(res, [])
        self.runner.docker_rm()

    @unittest.skipIf(
        os.environ['RUNTIME'] != 'docker',
        'Skipping docker tests...')
    def test_docker_build(self):
        pu.write_file('/tmp/test_folder/Dockerfile', """
        FROM debian:stable-slim

        RUN apt-get update && \
            apt-get install curl -y && \
            apt-get clean -y
        """)
        self.runner.docker_build('abcd:latest', '/tmp/test_folder')
        res = self.docker_client.images.get('abcd:latest')

    @unittest.skipIf(
        os.environ['RUNTIME'] != 'docker',
        'Skipping docker tests...')
    def test_docker_create(self):
        self.runner.action['args'] = ['env']
        self.runner.docker_pull('debian:buster-slim')
        self.runner.docker_create('debian:buster-slim')
        self.assertEqual(self.runner.docker_exists(), True)
        self.runner.docker_rm()


class TestSingularityRunner(unittest.TestCase):

    def setUp(self):
        os.makedirs('/tmp/test_folder')
        os.chdir('/tmp/test_folder')
        log.setLevel('CRITICAL')
        workflow = """
        workflow "sample" {
            resolves = "sample action"
        }

        action "sample action" {
            uses = "popperized/bin/sh@master"
            args = ["echo", "Hello"]
        }
        """
        pu.write_file('/tmp/test_folder/a.workflow', workflow)
        self.wf = Workflow('/tmp/test_folder/a.workflow')
        self.wf.parse()
        WorkflowRunner.download_actions(self.wf, False, False, '12345')
        WorkflowRunner.instantiate_runners(
            'singularity', self.wf, '/tmp/test_folder', False, False, '12345')
        self.runner = self.wf.action['sample action']['runner']
        SingularityRunner.setup_singularity_cache('12345')

    def tearDown(self):
        os.chdir('/tmp')
        shutil.rmtree('/tmp/test_folder')
        shutil.rmtree(os.path.join(os.environ['HOME'], '.cache/.popper'))
        log.setLevel('NOTSET')

    @unittest.skipIf(
        os.environ['RUNTIME'] != 'singularity',
        'Skipping singularity tests...')
    def test_singularity_exists(self):
        pu.write_file('/tmp/test_folder/testimg.sif', 'fake image file')
        self.assertEqual(
            self.runner.singularity_exists('/tmp/test_folder/testimg.sif'),
            True)
        os.remove('/tmp/test_folder/testimg.sif')

    @unittest.skipIf(
        os.environ['RUNTIME'] != 'singularity',
        'Skipping singularity tests...')
    def test_singularity_rm(self):
        pu.write_file('/tmp/test_folder/testimg.sif', 'fake image file')
        self.runner.singularity_rm('/tmp/test_folder/testimg.sif')
        self.assertEqual(self.runner.singularity_exists(
            '/tmp/test_folder/testimg.sif'), False)

    @unittest.skipIf(
        os.environ['RUNTIME'] != 'singularity',
        'Skipping singularity tests...')
    def test_singularity_build_from_image(self):
        self.runner.singularity_build_from_image(
            'docker://debian:buster-slim',
            os.path.join(
                os.environ['HOME'],
                '.cache/.popper/singularity/12345/testimg.sif'))
        self.assertEqual(
            os.path.exists(
                os.path.join(
                    os.environ['HOME'],
                    '.cache/.popper/singularity/12345/testimg.sif')),
            True)
        os.remove(
            os.path.join(
                os.environ['HOME'],
                '.cache/.popper/singularity/12345/testimg.sif'))
        self.runner.skip_pull = True
        self.assertRaises(
            SystemExit,
            self.runner.singularity_build_from_image,
            'docker://debian:buster-slim',
            os.path.join(
                os.environ['HOME'],
                '.cache/.popper/singularity/12345/testimg.sif'))

    @unittest.skipIf(
        os.environ['RUNTIME'] != 'singularity',
        'Skipping singularity tests...')
    def test_singularity_build_from_recipe(self):
        os.chdir(
            os.path.join(
                os.environ['HOME'],
                '.cache/.popper/actions/12345/github.com/popperized/bin/sh'))
        self.runner.singularity_build_from_recipe(
            os.path.join(
                os.environ['HOME'],
                '.cache/.popper/actions/12345/github.com/popperized/bin/sh'),
            os.path.join(
                os.environ['HOME'],
                '.cache/.popper/singularity/12345/testimg.sif'))
        self.assertEqual(
            os.path.exists(
                os.path.join(
                    os.environ['HOME'],
                    '.cache/.popper/singularity/12345/testimg.sif')),
            True)

    @unittest.skipIf(
        os.environ['RUNTIME'] != 'singularity',
        'Skipping singularity tests...')
    def test_get_recipe_file(self):
        os.chdir(
            os.environ['HOME'] +
            '/.cache/.popper/actions/12345/github.com/popperized/bin/sh')
        file = SingularityRunner.get_recipe_file(os.getcwd(), '12345')
        self.assertEqual(
            file,
            os.environ['HOME'] +
            '/.cache/.popper/actions/12345/github.com/popperized/bin/sh/' +
            'Singularity.12345')
        os.remove(
            os.environ['HOME'] +
            '/.cache/.popper/actions/12345/github.com/popperized/bin/sh/' +
            'Dockerfile')
        self.assertRaises(
            SystemExit,
            SingularityRunner.get_recipe_file,
            os.getcwd(),
            '12345')

    @unittest.skipIf(
        os.environ['RUNTIME'] != 'singularity',
        'Skipping singularity tests...')
    def test_singularity_start(self):
        self.runner.action['runs'] = [
            "sh", "-c", "echo 'Hello from Popper 2.x !' > popper.file"
        ]
        self.runner.singularity_build_from_image(
            'docker://debian:buster-slim',
            os.path.join(
                os.environ['HOME'],
                '.cache/.popper/singularity/12345/testimg.sif'))
        e = self.runner.singularity_start(
            os.path.join(
                os.environ['HOME'],
                '.cache/.popper/singularity/12345/testimg.sif'))
        self.assertEqual(e, 0)
        self.assertEqual(os.path.exists('popper.file'), True)

    @unittest.skipIf(
        os.environ['RUNTIME'] != 'singularity',
        'Skipping singularity tests...')
    def test_get_build_resources(self):
        res = self.runner.get_build_resources()
        self.assertTupleEqual(
            res,
            (True,
             'popperized/bin/sh@master',
             os.path.join(
                 os.environ['HOME'],
                 '.cache/.popper/actions/12345/github.com/popperized/bin/sh')))
        self.runner.action['uses'] = 'docker://debian:buster-slim'
        res = self.runner.get_build_resources()
        self.assertTupleEqual(res,
                              (False, 'docker://debian:buster-slim', None))
        self.runner.action['uses'] = './actions/jshint'
        res = self.runner.get_build_resources()
        self.assertTupleEqual(
            res,
            (True,
             'action/./actions/jshint',
             '/tmp/test_folder/./actions/jshint'))

    @unittest.skipIf(
        os.environ['RUNTIME'] != 'singularity',
        'Skipping singularity tests...')
    def test_setup_singularity_cache(self):
        cache_path = os.path.join(
            os.environ['HOME'],
            '.cache/.popper/singularity/12345')
        shutil.rmtree(cache_path)
        self.assertEqual(os.path.exists(cache_path), False)
        SingularityRunner.setup_singularity_cache('12345')
        self.assertEqual(os.path.exists(cache_path), True)


class TestHostRunner(unittest.TestCase):

    def setUp(self):
        os.makedirs('/tmp/test_folder')
        os.chdir('/tmp/test_folder')
        log.setLevel('CRITICAL')
        workflow = """
        workflow "sample" {
            resolves = "sample action"
        }

        action "sample action" {
            uses = "sh"
            args = ["echo", "Hello"]
        }
        """
        pu.write_file('/tmp/test_folder/a.workflow', workflow)
        self.wf = Workflow('/tmp/test_folder/a.workflow')
        self.wf.parse()
        WorkflowRunner.instantiate_runners(
            'docker', self.wf, '/tmp/test_folder', False, False, '12345')

    def tearDown(self):
        os.chdir('/tmp')
        shutil.rmtree('/tmp/test_folder')
        log.setLevel('NOTSET')

    def test_run(self):
        runner = self.wf.action['sample action']['runner']
        self.assertRaises(SystemExit, runner.run, reuse=True)
        runner.run()

    def test_host_prepare(self):
        runner = self.wf.action['sample action']['runner']
        runner.action['runs'] = ['script1']
        runner.action['args'] = ['github.com']
        cmd = runner.host_prepare()
        self.assertEqual(cmd, ['/tmp/test_folder/script1', 'github.com'])
        os.makedirs('/tmp/test_folder/action/myaction')
        runner.action['uses'] = './action/myaction'
        runner.action['runs'] = ['script']
        runner.action['args'] = ['arg1', 'arg2']
        cmd = runner.host_prepare()
        self.assertEqual(
            cmd, [
                '/tmp/test_folder/./action/myaction/./script', 'arg1', 'arg2'])
        os.chdir('/tmp/test_folder')
        runner.action.pop('runs')
        cmd = runner.host_prepare()
        self.assertEqual(
            cmd, [
                '/tmp/test_folder/./action/myaction/./entrypoint.sh',
                'arg1', 'arg2'])

    def test_host_start(self):
        runner = self.wf.action['sample action']['runner']
        runner.prepare_environment(set_env=True)
        e = runner.host_start([
            "sh", "-c", "echo 'Hello from Popper 2.x !' > popper.file"
        ])
        self.assertEqual(e, 0)
        self.assertEqual(os.path.exists('popper.file'), True)
        runner.remove_environment()


class TestConcurrentExecution(unittest.TestCase):

    def setUp(self):
        os.makedirs('/tmp/test_folder/gha-demo')
        # log.setLevel('CRITICAL')
        git.Repo.clone_from(
            'https://github.com/JayjeetAtGithub/popper-scaffold-workflow',
            '/tmp/test_folder/gha-demo')
        os.chdir('/tmp/test_folder/gha-demo')
        self.wf_one = Workflow('/tmp/test_folder/gha-demo/main.workflow')
        self.wf_two = Workflow('/tmp/test_folder/gha-demo/main.workflow')
        self.wf_three = Workflow('/tmp/test_folder/gha-demo/main.workflow')
        self.runner_one = WorkflowRunner(self.wf_one)
        self.runner_one.wid = '1234'
        self.runner_two = WorkflowRunner(self.wf_two)
        self.runner_two.wid = '5678'
        self.runner_three = WorkflowRunner(self.wf_three)
        self.runner_three.wid = '3456'

    def tearDown(self):
        os.chdir('/tmp')
        shutil.rmtree('/tmp/test_folder')
        # log.setLevel('NOTSET')

    def test_run(self):
        os.environ['PHONY_SECRET'] = '1234'
        args = (None, False, False, list(), '/tmp/test_folder/gha-demo',
                False, False, False, False, os.environ['RUNTIME'])
        with ThreadPoolExecutor(max_workers=mp.cpu_count()) as ex:
            flist = [
                ex.submit(self.runner_one.run, *args),
                ex.submit(self.runner_two.run, *args),
                ex.submit(self.runner_three.run, *args)]
