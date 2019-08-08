import os
import shutil
import unittest
try:
    from unittest.mock import patch
except ImportError:
    from mock import patch

import docker
import git

from popper.cli import log
from popper.parser import Workflow
from popper.gha import (WorkflowRunner,
                        ActionRunner,
                        DockerRunner,
                        SingularityRunner,
                        HostRunner)


class TestWorkflowRunner(unittest.TestCase):

    def setUp(self):
        os.makedirs('/tmp/test_folder')
        os.chdir('/tmp/test_folder')
        log.setLevel('CRITICAL')

    def tearDown(self):
        os.chdir('/tmp')
        shutil.rmtree('/tmp/test_folder')
        log.setLevel('NOTSET')

    def create_workflow_file(self, content):
        f = open('/tmp/test_folder/a.workflow', 'w')
        f.write(content)
        f.close()

    def create_file(self, path, content):
        f = open(path, 'w')
        f.write(content)
        f.close()

    def test_check_secrets(self):
        os.environ['SECRET_ONE'] = '1234'
        os.environ['SECRET_TWO'] = '5678'
        self.create_workflow_file("""
        workflow "sample" {
            resolves = "a"
        }

        action "a" {
            uses = "actions/bin/sh@master"
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
        self.create_workflow_file("""
        workflow "sample" {
            resolves = "a"
        }

        action "a" {
            uses = "actions/bin/sh@master"
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
        self.create_workflow_file("""
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
            'docker', wf, '/tmp/test_folder', False, False)
        self.assertIsInstance(wf.action['a']['runner'], HostRunner)

        os.makedirs('/tmp/test_folder/actions/sample')
        self.create_file('/tmp/test_folder/actions/sample/entrypoint.sh', '')
        self.create_file('/tmp/test_folder/actions/sample/README.md', '')

        self.create_workflow_file("""
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
            'singularity', wf, '/tmp/test_folder', False, False)
        self.assertIsInstance(wf.action['a']['runner'], HostRunner)

        self.create_workflow_file("""
        workflow "sample" {
            resolves = "a"
        }

        action "a" {
            uses = "actions/bin/sh@master"
        }
        """)
        wf = Workflow('/tmp/test_folder/a.workflow')
        wf.parse()
        env = WorkflowRunner.get_workflow_env(wf, '/tmp/test_folder')
        WorkflowRunner.instantiate_runners(
            'singularity', wf, '/tmp/test_folder', False, False)
        self.assertIsInstance(wf.action['a']['runner'], SingularityRunner)

        WorkflowRunner.instantiate_runners(
            'docker', wf, '/tmp/test_folder', False, False)
        self.assertIsInstance(wf.action['a']['runner'], DockerRunner)

    def test_download_actions(self):
        self.create_workflow_file("""
        workflow "sample" {
            resolves = "a"
        }

        action "a" {
            uses = "actions/bin/sh@master"
        }

        action "b" {
            uses = "popperized/ansible@master"
        }
        """)
        wf = Workflow('/tmp/test_folder/a.workflow')
        wf.parse()
        WorkflowRunner.download_actions(wf, False, False)

        shutil.rmtree('/tmp/actions/github.com')
        self.assertRaises(
            SystemExit,
            WorkflowRunner.download_actions,
            wf,
            False,
            True)

    def test_get_workflow_env(self):
        self.create_workflow_file("""
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


class TestDockerRunner(unittest.TestCase):

    def create_workflow_file(self, content):
        f = open('/tmp/test_folder/a.workflow', 'w')
        f.write(content)
        f.close()

    def create_file(self, path, content):
        f = open(path, 'w')
        f.write(content)
        f.close()

    def setUp(self):
        os.makedirs('/tmp/test_folder')
        os.chdir('/tmp/test_folder')
        log.setLevel('CRITICAL')
        workflow = """
        workflow "sample" {
            resolves = "sample action"
        }

        action "sample action" {
            uses = "actions/bin/sh@master"
            args = ["echo", "Hello"]
        }
        """
        self.create_workflow_file(workflow)
        self.wf = Workflow('/tmp/test_folder/a.workflow')
        self.wf.parse()
        WorkflowRunner.instantiate_runners(
            'docker', self.wf, '/tmp/test_folder', False, False)
        self.docker_client = docker.from_env()

    def tearDown(self):
        os.chdir('/tmp')
        shutil.rmtree('/tmp/test_folder')
        log.setLevel('NOTSET')
        self.docker_client.close()

    @unittest.skipIf(
        os.environ['RUNTIME'] != 'docker',
        'Skipping docker tests...')
    def test_docker_exists(self):
        image = self.docker_client.images.pull('debian:buster-slim')
        container = self.docker_client.containers.create(
            image='debian:buster-slim',
            name='popper_sample_action')
        runner = self.wf.action['sample action']['runner']
        self.assertEqual(runner.docker_exists(), True)
        container.remove()
        self.docker_client.images.remove('debian:buster-slim')

    @unittest.skipIf(
        os.environ['RUNTIME'] != 'docker',
        'Skipping docker tests...')
    def test_docker_image_exists(self):
        image = self.docker_client.images.pull('debian:buster-slim')
        runner = self.wf.action['sample action']['runner']
        self.assertEqual(runner.docker_image_exists(
            'debian:buster-slim'), True)
        self.docker_client.images.remove('debian:buster-slim', force=True)

    @unittest.skipIf(
        os.environ['RUNTIME'] != 'docker',
        'Skipping docker tests...')
    def test_docker_rm(self):
        self.docker_client.images.pull('debian:buster-slim')
        runner = self.wf.action['sample action']['runner']
        runner.docker_create('debian:buster-slim')
        runner.docker_rm()
        self.assertRaises(docker.errors.NotFound, runner.docker_rm)

    @unittest.skipIf(
        os.environ['RUNTIME'] != 'docker',
        'Skipping docker tests...')
    def test_docker_pull(self):
        runner = self.wf.action['sample action']['runner']
        self.assertEqual(runner.docker_image_exists(
            'debian:buster-slim'), False)
        runner.skip_pull = True
        self.assertRaises(SystemExit, runner.docker_pull, 'debian:buster-slim')
        runner.skip_pull = False
        runner.docker_pull('debian:buster-slim')
        self.assertEqual(runner.docker_image_exists(
            'debian:buster-slim'), True)

    @unittest.skipIf(
        os.environ['RUNTIME'] != 'docker',
        'Skipping docker tests...')
    def test_docker_start(self):
        runner = self.wf.action['sample action']['runner']
        runner.action['runs'] = [
            "sh", "-c", "echo 'Hello from Popper 2.x !' > popper.file"
        ]
        runner.docker_pull('debian:buster-slim')
        runner.docker_create('debian:buster-slim')
        e = runner.docker_start()
        self.assertEqual(e, 0)
        self.assertEqual(os.path.exists('popper.file'), True)
        res = self.docker_client.containers.list(filters={'status': 'running'})
        self.assertListEqual(res, [])
        runner.docker_rm()

    @unittest.skipIf(
        os.environ['RUNTIME'] != 'docker',
        'Skipping docker tests...')
    def test_docker_build(self):
        self.create_file('/tmp/test_folder/Dockerfile', """
        FROM debian:stable-slim

        RUN apt-get update && \
            apt-get install curl -y && \
            apt-get clean -y
        """)
        runner = self.wf.action['sample action']['runner']
        runner.docker_build('abcd:latest', '/tmp/test_folder')
        res = self.docker_client.images.get('abcd:latest')

    @unittest.skipIf(
        os.environ['RUNTIME'] != 'docker',
        'Skipping docker tests...')
    def test_docker_create(self):
        runner = self.wf.action['sample action']['runner']
        runner.action['args'] = ['env']
        runner.docker_pull('debian:buster-slim')
        runner.docker_create('debian:buster-slim')
        self.assertEqual(runner.docker_exists(), True)
        runner.docker_rm()

    def test_prepare_environment(self):
        runner = self.wf.action['sample action']['runner']
        env = runner.prepare_environment()
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
        env = runner.prepare_environment(set_env=True)
        self.assertEqual(set(env.keys()).issubset(set(os.environ)), True)
        runner.remove_environment()

    def test_remove_environment(self):
        runner = self.wf.action['sample action']['runner']
        env = runner.prepare_environment(set_env=True)
        self.assertEqual(set(env.keys()).issubset(set(os.environ)), True)
        runner.remove_environment()
        self.assertEqual(set(env.keys()).issubset(set(os.environ)), False)

    def test_setup_necessary_files(self):
        runner = self.wf.action['sample action']['runner']
        os.remove('/tmp/github_event.json')
        self.assertEqual(os.path.exists('/tmp/github_event.json'), False)
        runner.setup_necessary_files()
        self.assertEqual(os.path.exists('/tmp/github_event.json'), True)
        runner.workspace = '/tmp/a/b/c'
        runner.setup_necessary_files()
        self.assertEqual(os.path.exists('/tmp/a/b/c'), True)


class TestSingularityRunner(unittest.TestCase):

    def create_workflow_file(self, content):
        f = open('/tmp/test_folder/a.workflow', 'w')
        f.write(content)
        f.close()

    def create_file(self, path, content):
        f = open(path, 'w')
        f.write(content)
        f.close()

    def setUp(self):
        os.makedirs('/tmp/test_folder')
        os.makedirs('/tmp/singularity')
        os.chdir('/tmp/test_folder')
        log.setLevel('CRITICAL')
        workflow = """
        workflow "sample" {
            resolves = "sample action"
        }

        action "sample action" {
            uses = "actions/bin/sh@master"
            args = ["echo", "Hello"]
        }
        """
        self.create_workflow_file(workflow)
        self.wf = Workflow('/tmp/test_folder/a.workflow')
        self.wf.parse()
        WorkflowRunner.instantiate_runners(
            'singularity', self.wf, '/tmp/test_folder', False, False)
        self.docker_client = docker.from_env()

    def tearDown(self):
        os.chdir('/tmp')
        shutil.rmtree('/tmp/test_folder')
        shutil.rmtree('/tmp/singularity')
        log.setLevel('NOTSET')

    @unittest.skipIf(
        os.environ['RUNTIME'] != 'singularity',
        'Skipping singularity tests...')
    def test_singularity_exists(self):
        self.create_file('/tmp/test_folder/testimg.sif', 'fake image file')
        runner = self.wf.action['sample action']['runner']
        self.assertEqual(
            runner.singularity_exists('/tmp/test_folder/testimg.sif'),
            True)
        os.remove('/tmp/test_folder/testimg.sif')

    @unittest.skipIf(
        os.environ['RUNTIME'] != 'singularity',
        'Skipping singularity tests...')
    def test_singularity_rm(self):
        self.create_file('/tmp/test_folder/testimg.sif', 'fake image file')
        runner = self.wf.action['sample action']['runner']
        runner.singularity_rm('/tmp/test_folder/testimg.sif')
        self.assertEqual(
            runner.singularity_exists('/tmp/test_folder/testimg.sif'), False
        )

    @unittest.skipIf(
        os.environ['RUNTIME'] != 'singularity',
        'Skipping singularity tests...')
    def test_singularity_build_from_image(self):
        runner = self.wf.action['sample action']['runner']
        runner.singularity_build_from_image(
            'docker://debian:buster-slim',
            'testimg.sif',
            '/tmp/singularity/testimg.sif')
        self.assertEqual(os.path.exists('/tmp/singularity/testimg.sif'), True)
        os.remove('/tmp/singularity/testimg.sif')
        runner.skip_pull = True
        self.assertRaises(
            SystemExit,
            runner.singularity_build_from_image,
            'docker://debian:buster-slim',
            'testimg.sif',
            '/tmp/singularity/testimg.sif')

    @unittest.skipIf(
        os.environ['RUNTIME'] != 'singularity',
        'Skipping singularity tests...')
    def test_singularity_build_from_recipe(self):
        runner = self.wf.action['sample action']['runner']
        os.mkdir('/tmp/test_folder/bin')
        git.Repo.clone_from(
            'https://github.com/actions/bin',
            '/tmp/test_folder/bin')
        os.chdir('/tmp/test_folder/bin/sh')
        runner.singularity_build_from_recipe(
            '/tmp/test_folder/bin/sh',
            'testimg.sif',
            '/tmp/singularity/testimg.sif')
        self.assertEqual(os.path.exists(
            '/tmp/singularity/testimg.sif'), True)
        os.remove('/tmp/singularity/testimg.sif')
        os.chdir('/tmp/test_folder')

    @unittest.skipIf(
        os.environ['RUNTIME'] != 'singularity',
        'Skipping singularity tests...')
    def test_get_recipe_file(self):
        os.makedirs('/tmp/test_folder/bin')
        git.Repo.clone_from(
            'https://github.com/actions/bin',
            '/tmp/test_folder/bin')
        os.chdir('/tmp/test_folder/bin/sh')
        file = SingularityRunner.get_recipe_file(os.getcwd(), 'abcd.sif')
        self.assertEqual(file, '/tmp/test_folder/bin/sh/Singularity.abcd')
        os.remove('/tmp/test_folder/bin/sh/Dockerfile')
        self.assertRaises(
            SystemExit,
            SingularityRunner.get_recipe_file,
            os.getcwd(),
            'abcd.sif')

    @unittest.skipIf(
        os.environ['RUNTIME'] != 'singularity',
        'Skipping singularity tests...')
    def test_singularity_start(self):
        runner = self.wf.action['sample action']['runner']
        runner.action['runs'] = [
            "sh", "-c", "echo 'Hello from Popper 2.x !' > popper.file"
        ]
        runner.singularity_build_from_image(
            'docker://debian:buster-slim',
            'testimg.sif',
            '/tmp/singularity/testimg.sif')
        e = runner.singularity_start('/tmp/singularity/testimg.sif')
        self.assertEqual(e, 0)
        self.assertEqual(os.path.exists('popper.file'), True)


class TestHostRunner(unittest.TestCase):

    def create_workflow_file(self, content):
        f = open('/tmp/test_folder/a.workflow', 'w')
        f.write(content)
        f.close()

    def create_file(self, path, content):
        f = open(path, 'w')
        f.write(content)
        f.close()

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
        self.create_workflow_file(workflow)
        self.wf = Workflow('/tmp/test_folder/a.workflow')
        self.wf.parse()
        WorkflowRunner.instantiate_runners(
            'docker', self.wf, '/tmp/test_folder', False, False)

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
