import os
import signal
import shutil
import unittest
import multiprocessing as mp

import docker
import git
import vagrant
import warnings

from unittest.mock import patch
from popper.cli import log
from popper.parser import HCLWorkflow
from popper.gha import (WorkflowRunner,
                        DockerRunner,
                        SingularityRunner,
                        VagrantRunner,
                        HostRunner)
from concurrent.futures import ThreadPoolExecutor
import popper.utils as pu


class TestWorkflowRunner(unittest.TestCase):

    def setUp(self):
        warnings.filterwarnings(action="ignore", message="unclosed",
                                category=ResourceWarning)
        os.makedirs('/tmp/test_folder', exist_ok=True)
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
        wf = HCLWorkflow('/tmp/test_folder/a.workflow')
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
        wf = HCLWorkflow('/tmp/test_folder/a.workflow')
        wf.parse()
        os.environ['CI'] = 'false'
        with patch('getpass.getpass', return_value='1234'):
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
        wf = HCLWorkflow('/tmp/test_folder/a.workflow')
        wf.parse()
        WorkflowRunner.instantiate_runners(
            'docker', wf, '/tmp/test_folder', False, False, '12345')
        self.assertIsInstance(wf.step['a']['runner'], HostRunner)

        os.makedirs('/tmp/test_folder/steps/sample')
        pu.write_file('/tmp/test_folder/steps/sample/entrypoint.sh')
        pu.write_file('/tmp/test_folder/steps/sample/README.md')

        pu.write_file('/tmp/test_folder/a.workflow', """
        workflow "sample" {
            resolves = "a"
        }

        action "a" {
            uses = "./steps/sample"

        }
        """)
        wf = HCLWorkflow('/tmp/test_folder/a.workflow')
        wf.parse()
        WorkflowRunner.instantiate_runners(
            'singularity', wf, '/tmp/test_folder', False, False, '12345')
        self.assertIsInstance(wf.step['a']['runner'], HostRunner)

        pu.write_file('/tmp/test_folder/a.workflow', """
        workflow "sample" {
            resolves = "a"
        }

        action "a" {
            uses = "popperized/bin/sh@master"
        }
        """)
        wf = HCLWorkflow('/tmp/test_folder/a.workflow')
        wf.parse()
        WorkflowRunner.instantiate_runners(
            'singularity', wf, '/tmp/test_folder', False, False, '12345')
        self.assertIsInstance(wf.step['a']['runner'], SingularityRunner)

        WorkflowRunner.instantiate_runners(
            'docker', wf, '/tmp/test_folder', False, False, '12345')
        self.assertIsInstance(wf.step['a']['runner'], DockerRunner)

        WorkflowRunner.instantiate_runners(
            'vagrant', wf, '/tmp/test_folder', False, False, '12345')
        self.assertIsInstance(wf.step['a']['runner'], VagrantRunner)

    def test_download_steps(self):
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
        wf = HCLWorkflow('/tmp/test_folder/a.workflow')
        wf.parse()

        # Download steps in the default cache directory.
        WorkflowRunner.download_steps(wf, False, False, '12345')
        self.assertEqual(
            os.path.exists(
                os.environ['HOME'] +
                '/.cache/popper/steps/12345/github.com'),
            True)

        # Download steps in custom cache directory
        os.environ['POPPER_CACHE_DIR'] = '/tmp/somedir'
        WorkflowRunner.download_steps(wf, False, False, '12345')
        self.assertEqual(os.path.exists(
            '/tmp/somedir/steps/12345/github.com'), True)
        os.environ.pop('POPPER_CACHE_DIR')

        # Release resources.
        shutil.rmtree('/tmp/somedir')
        shutil.rmtree(
            os.environ['HOME'] +
            '/.cache/popper/steps/12345/github.com')

        # Test with skipclone flag when step not present in cache.
        self.assertRaises(
            SystemExit,
            WorkflowRunner.download_steps,
            wf,
            False,
            True,
            '12345')


class TestStepRunner(unittest.TestCase):

    def setUp(self):
        warnings.filterwarnings(action="ignore", message="unclosed",
                                category=ResourceWarning)
        os.makedirs('/tmp/test_folder', exist_ok=True)
        os.chdir('/tmp/test_folder')
        log.setLevel('CRITICAL')
        workflow = """
        workflow "sample" {
            resolves = "sample action"
        }

        action "sample action" {
            uses = "popperized/bin/sh@master"
            args = ["echo", "Hello"]
            env = {
              FOOBAR = "yeah"
            }
        }
        """
        pu.write_file('/tmp/test_folder/a.workflow', workflow)
        self.wf = HCLWorkflow('/tmp/test_folder/a.workflow')
        self.wf.parse()
        WorkflowRunner.instantiate_runners(
            'docker', self.wf, '/tmp/test_folder', False, False, '12345')
        self.runner = self.wf.step['sample action']['runner']

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
        self.assertDictEqual(env, {'FOOBAR': 'yeah'})

    def test_prepare_volumes(self):
        volumes = self.runner.prepare_volumes()
        self.assertEqual(volumes, [
            '/tmp/test_folder:/workspace'])
        volumes = self.runner.prepare_volumes(include_docker_socket=True)
        self.assertEqual(volumes, [
            '/tmp/test_folder:/workspace',
            '/var/run/docker.sock:/var/run/docker.sock'])

    def test_setup_necessary_files(self):
        self.runner.workspace = '/tmp/a/b/c'
        self.runner.setup_necessary_files()
        self.assertEqual(os.path.exists('/tmp/a/b/c'), True)


class TestDockerRunner(unittest.TestCase):

    def setUp(self):
        warnings.filterwarnings(action="ignore", message="unclosed",
                                category=ResourceWarning)
        os.makedirs('/tmp/test_folder', exist_ok=True)
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
        self.wf = HCLWorkflow('/tmp/test_folder/a.workflow')
        self.wf.parse()
        WorkflowRunner.download_steps(self.wf, False, False, '12345')
        WorkflowRunner.instantiate_runners(
            'docker', self.wf, '/tmp/test_folder', False, False, '12345')
        self.docker_client = docker.from_env()
        self.runner = self.wf.step['sample action']['runner']

    def tearDown(self):
        os.chdir('/tmp')
        shutil.rmtree('/tmp/test_folder')
        shutil.rmtree(os.path.join(os.environ['HOME'], '.cache/popper'))
        log.setLevel('NOTSET')
        self.docker_client.close()

    @unittest.skipIf(
        os.environ['ENGINE'] != 'docker',
        'Skipping docker tests...')
    def test_get_build_resources(self):
        res = self.runner.get_build_resources()
        self.assertTupleEqual(
            res,
            (True,
             'popperized/bin:master',
             os.environ['HOME'] +
             '/.cache/popper/steps/12345/github.com/popperized/bin/sh'))
        self.runner.step['uses'] = 'docker://alpine:3.8'
        res = self.runner.get_build_resources()
        self.assertTupleEqual(res,
                              (False, 'alpine:3.8', None))
        self.runner.step['uses'] = './actions/jshint'
        res = self.runner.get_build_resources()
        self.assertTupleEqual(
            res, (True, 'jshint:unknown', '/tmp/test_folder/./actions/jshint'))

    @unittest.skipIf(
        os.environ['ENGINE'] != 'docker',
        'Skipping docker tests...')
    def test_docker_exists(self):
        self.docker_client.images.pull('alpine:3.8')
        container = self.docker_client.containers.create(
            image='alpine:3.8',
            name='popper_sample_action_12345')
        self.assertEqual(self.runner.docker_exists(), True)
        container.remove()
        self.docker_client.images.remove('alpine:3.8')

    @unittest.skipIf(os.environ['ENGINE'] != 'docker', 'Skipping docker...')
    def test_docker_image_exists(self):
        self.docker_client.images.pull('alpine:3.8')
        self.runner.docker_pull('alpine:3.8')
        self.assertEqual(self.runner.docker_image_exists('alpine:3.8'),
                         True)
        self.docker_client.images.remove('alpine:3.8', force=True)

    @unittest.skipIf(
        os.environ['ENGINE'] != 'docker',
        'Skipping docker tests...')
    def test_docker_rm(self):
        self.docker_client.images.pull('alpine:3.8')
        self.runner.docker_create('alpine:3.8')
        self.runner.docker_rm()
        self.assertRaises(docker.errors.NotFound, self.runner.docker_rm)

    @unittest.skipIf(
        os.environ['ENGINE'] != 'docker',
        'Skipping docker tests...')
    def test_docker_pull(self):
        self.assertEqual(self.runner.docker_image_exists('alpine:3.8'), False)
        self.runner.skip_pull = True
        self.assertRaises(SystemExit, self.runner.docker_pull, 'alpine:3.8')
        self.runner.skip_pull = False
        self.runner.docker_pull('alpine:3.8')
        self.assertEqual(self.runner.docker_image_exists('alpine:3.8'), True)

    @unittest.skipIf(
        os.environ['ENGINE'] != 'docker',
        'Skipping docker tests...')
    def test_docker_start(self):
        self.runner.step['runs'] = [
            "sh", "-c", "echo 'Hello from Popper 2.x !' > popper.file"
        ]
        self.runner.docker_pull('alpine:3.8')
        self.runner.docker_create('alpine:3.8')
        e = self.runner.docker_start()
        self.assertEqual(e, 0)
        self.assertEqual(os.path.exists('popper.file'), True)
        res = self.docker_client.containers.list(filters={'status': 'running'})
        self.assertListEqual(res, [])
        self.runner.docker_rm()

    @unittest.skipIf(
        os.environ['ENGINE'] != 'docker',
        'Skipping docker tests...')
    def test_docker_build(self):
        pu.write_file('/tmp/test_folder/Dockerfile', """
        FROM debian:stable-slim

        RUN apt-get update && \
            apt-get install curl -y && \
            apt-get clean -y
        """)
        self.runner.docker_build('abcd:latest', '/tmp/test_folder')

    @unittest.skipIf(
        os.environ['ENGINE'] != 'docker',
        'Skipping docker tests...')
    def test_mix_with_engine_conf(self):
        config = {
            "image": "popperized/bin",
            "command": "ls -l",
            "name": "popper_bin",
            "volumes": ["/tmp:/tmp"],
            "working_dir": "/workspace",
            "environment": {
                "A": "a", "B": "b"
            },
            "entrypoint": None,
            "detach": True
        }

        self.runner.engine_conf = {
            "volumes": ["/var:/var"],
            "environment": {
                "C": "c"
            },
            "hostname": "abc.local",
            "privileged": True
        }

        result_config = {
            'image': 'popperized/bin',
            'command': 'ls -l',
            'name': 'popper_bin',
            'volumes': ['/tmp:/tmp', '/var:/var'],
            'working_dir': '/workspace',
            'environment': {'A': 'a', 'B': 'b', 'C': 'c'},
            'entrypoint': None,
            'detach': True,
            'hostname': 'abc.local',
            'privileged': True
        }

        config = self.runner.mix_with_engine_conf(config)
        self.assertEqual(config, result_config)

    @unittest.skipIf(
        os.environ['ENGINE'] != 'docker',
        'Skipping docker tests...')
    def test_docker_create(self):
        self.runner.step['args'] = ['env']
        self.runner.docker_pull('alpine:3.8')
        self.runner.docker_create('alpine:3.8')
        self.assertEqual(self.runner.docker_exists(), True)
        self.runner.docker_rm()


class TestSingularityRunner(unittest.TestCase):

    def setUp(self):
        warnings.filterwarnings(action="ignore", message="unclosed",
                                category=ResourceWarning)
        os.makedirs('/tmp/test_folder', exist_ok=True)
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
        self.wf = HCLWorkflow('/tmp/test_folder/a.workflow')
        self.wf.parse()
        WorkflowRunner.download_steps(self.wf, False, False, '12345')
        WorkflowRunner.instantiate_runners(
            'singularity', self.wf, '/tmp/test_folder', False, False, '12345')
        self.runner = self.wf.step['sample action']['runner']
        SingularityRunner.setup_singularity_cache('12345')

    def tearDown(self):
        os.chdir('/tmp')
        shutil.rmtree('/tmp/test_folder')
        shutil.rmtree(os.path.join(os.environ['HOME'], '.cache/popper'))
        log.setLevel('NOTSET')

    @unittest.skipIf(
        os.environ['ENGINE'] != 'singularity',
        'Skipping singularity tests...')
    def test_singularity_exists(self):
        pu.write_file('/tmp/test_folder/testimg.sif', 'fake image file')
        self.assertEqual(
            self.runner.singularity_exists('/tmp/test_folder/testimg.sif'),
            True)
        os.remove('/tmp/test_folder/testimg.sif')

    @unittest.skipIf(
        os.environ['ENGINE'] != 'singularity',
        'Skipping singularity tests...')
    def test_singularity_rm(self):
        pu.write_file('/tmp/test_folder/testimg.sif', 'fake image file')
        self.runner.singularity_rm('/tmp/test_folder/testimg.sif')
        self.assertEqual(self.runner.singularity_exists(
            '/tmp/test_folder/testimg.sif'), False)

    @unittest.skipIf(
        os.environ['ENGINE'] != 'singularity',
        'Skipping singularity tests...')
    def test_singularity_build_from_image(self):
        self.runner.singularity_build_from_image(
            'docker://alpine:3.8',
            os.path.join(
                os.environ['HOME'],
                '.cache/popper/singularity/12345/testimg.sif'))
        self.assertEqual(
            os.path.exists(
                os.path.join(
                    os.environ['HOME'],
                    '.cache/popper/singularity/12345/testimg.sif')),
            True)
        os.remove(
            os.path.join(
                os.environ['HOME'],
                '.cache/popper/singularity/12345/testimg.sif'))
        self.runner.skip_pull = True
        self.assertRaises(
            SystemExit,
            self.runner.singularity_build_from_image,
            'docker://alpine:3.8',
            os.path.join(
                os.environ['HOME'],
                '.cache/popper/singularity/12345/testimg.sif'))

    @unittest.skipIf(
        os.environ['ENGINE'] != 'singularity',
        'Skipping singularity tests...')
    def test_singularity_build_from_recipe(self):
        os.chdir(
            os.path.join(
                os.environ['HOME'],
                '.cache/popper/steps/12345/github.com/popperized/bin/sh'))
        self.runner.singularity_build_from_recipe(
            os.path.join(
                os.environ['HOME'],
                '.cache/popper/steps/12345/github.com/popperized/bin/sh'),
            os.path.join(
                os.environ['HOME'],
                '.cache/popper/singularity/12345/testimg.sif'))
        self.assertEqual(
            os.path.exists(
                os.path.join(
                    os.environ['HOME'],
                    '.cache/popper/singularity/12345/testimg.sif')),
            True)

    @unittest.skipIf(
        os.environ['ENGINE'] != 'singularity',
        'Skipping singularity tests...')
    def test_get_recipe_file(self):
        os.chdir(
            os.environ['HOME'] +
            '/.cache/popper/steps/12345/github.com/popperized/bin/sh')
        file = SingularityRunner.get_recipe_file(os.getcwd(), '12345')
        self.assertEqual(
            file,
            os.environ['HOME'] +
            '/.cache/popper/steps/12345/github.com/popperized/bin/sh/' +
            'Singularity.12345')
        os.remove(
            os.environ['HOME'] +
            '/.cache/popper/steps/12345/github.com/popperized/bin/sh/' +
            'Dockerfile')
        self.assertRaises(
            SystemExit,
            SingularityRunner.get_recipe_file,
            os.getcwd(),
            '12345')

    @unittest.skipIf(
        os.environ['ENGINE'] != 'singularity',
        'Skipping singularity tests...')
    def test_singularity_start(self):
        self.runner.step['runs'] = [
            "sh", "-c", "echo 'Hello from Popper 2.x !' > popper.file"
        ]
        self.runner.singularity_build_from_image(
            'docker://alpine:3.8',
            os.path.join(
                os.environ['HOME'],
                '.cache/popper/singularity/12345/testimg.sif'))
        e = self.runner.singularity_start(
            os.path.join(
                os.environ['HOME'],
                '.cache/popper/singularity/12345/testimg.sif'))
        self.assertEqual(e, 0)
        self.assertEqual(os.path.exists('popper.file'), True)

    @unittest.skipIf(
        os.environ['ENGINE'] != 'singularity',
        'Skipping singularity tests...')
    def test_get_build_resources(self):
        res = self.runner.get_build_resources()
        self.assertTupleEqual(
            res,
            (True,
             'popperized/bin/sh@master',
             os.path.join(
                 os.environ['HOME'],
                 '.cache/popper/steps/12345/github.com/popperized/bin/sh')))
        self.runner.step['uses'] = 'docker://alpine:3.8'
        res = self.runner.get_build_resources()
        self.assertTupleEqual(res, (False, 'docker://alpine:3.8', None))
        self.runner.step['uses'] = './actions/jshint'
        res = self.runner.get_build_resources()
        self.assertTupleEqual(
            res,
            (True,
             'action/./actions/jshint',
             '/tmp/test_folder/./actions/jshint'))

    @unittest.skipIf(
        os.environ['ENGINE'] != 'singularity',
        'Skipping singularity tests...')
    def test_setup_singularity_cache(self):
        cache_path = os.path.join(
            os.environ['HOME'],
            '.cache/popper/singularity/12345')
        shutil.rmtree(cache_path)
        self.assertEqual(os.path.exists(cache_path), False)
        SingularityRunner.setup_singularity_cache('12345')
        self.assertEqual(os.path.exists(cache_path), True)


class TestVagrantRunner(unittest.TestCase):

    def setUp(self):
        warnings.filterwarnings(action="ignore", message="unclosed",
                                category=ResourceWarning)
        os.makedirs('/tmp/test_folder', exist_ok=True)
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
        self.wf = HCLWorkflow('/tmp/test_folder/a.workflow')
        self.wf.parse()
        WorkflowRunner.download_steps(self.wf, False, False, '12345')
        WorkflowRunner.instantiate_runners(
            'vagrant', self.wf, '/tmp/test_folder', False, False, '12345')
        self.runner = self.wf.step['sample action']['runner']
        VagrantRunner.setup_vagrant_cache('12345')

    def tearDown(self):
        os.chdir('/tmp')
        shutil.rmtree('/tmp/test_folder')
        log.setLevel('NOTSET')

    @unittest.skipIf(
        os.environ['ENGINE'] != 'vagrant',
        'Skipping vagrant tests...')
    def test_setup_vagrant_cache(self):
        cache_path = os.path.join(
            os.environ['HOME'],
            '.cache/popper/vagrant/12345')
        shutil.rmtree(cache_path)
        self.assertEqual(os.path.exists(cache_path), False)
        VagrantRunner.setup_vagrant_cache('12345')
        self.assertEqual(os.path.exists(cache_path), True)

    @unittest.skipIf(
        os.environ['ENGINE'] != 'vagrant',
        'Skipping vagrant tests...')
    def test_vagrant_start(self):
        os.makedirs('/tmp/test_folder/test_vm', exist_ok=True)
        vagrantfile_content = """
        Vagrant.configure("2") do |config|
            config.vm.box = "ailispaw/barge"
        end
        """
        pu.write_file(
            '/tmp/test_folder/test_vm/Vagrantfile',
            vagrantfile_content)
        self.runner.vagrant_start('/tmp/test_folder/test_vm')
        self.assertEqual(self.runner.vagrant_exists(
            '/tmp/test_folder/test_vm'), True)
        vagrant.Vagrant(root='/tmp/test_folder/test_vm').halt()
        vagrant.Vagrant(root='/tmp/test_folder/test_vm').destroy()

    @unittest.skipIf(
        os.environ['ENGINE'] != 'vagrant',
        'Skipping vagrant tests...')
    def test_vagrant_stop(self):
        os.makedirs('/tmp/test_folder/test_vm', exist_ok=True)
        vagrantfile_content = """
        Vagrant.configure("2") do |config|
            config.vm.box = "ailispaw/barge"
        end
        """
        pu.write_file(
            '/tmp/test_folder/test_vm/Vagrantfile',
            vagrantfile_content)
        v = vagrant.Vagrant(root='/tmp/test_folder/test_vm')
        v.up()
        self.assertEqual(self.runner.vagrant_exists(
            '/tmp/test_folder/test_vm'), True)
        self.runner.vagrant_stop('/tmp/test_folder/test_vm')
        self.assertEqual(self.runner.vagrant_exists(
            '/tmp/test_folder/test_vm'), False)
        vagrant.Vagrant(root='/tmp/test_folder/test_vm').destroy()

    @unittest.skipIf(
        os.environ['ENGINE'] != 'vagrant',
        'Skipping vagrant tests...')
    def test_vagrant_exists(self):
        os.makedirs('/tmp/test_folder/test_vm', exist_ok=True)
        vagrantfile_content = """
        Vagrant.configure("2") do |config|
            config.vm.box = "ailispaw/barge"
        end
        """
        pu.write_file(
            '/tmp/test_folder/test_vm/Vagrantfile',
            vagrantfile_content)
        v = vagrant.Vagrant(root='/tmp/test_folder/test_vm')
        v.up()
        self.assertEqual(self.runner.vagrant_exists(
            '/tmp/test_folder/test_vm'), True)
        v.halt()
        self.assertEqual(self.runner.vagrant_exists(
            '/tmp/test_folder/test_vm'), False)
        vagrant.Vagrant(root='/tmp/test_folder/test_vm').destroy()
        shutil.rmtree('/tmp/test_folder/test_vm')
        self.assertEqual(self.runner.vagrant_exists(
            '/tmp/test_folder/test_vm'), False)

    @unittest.skipIf(
        os.environ['ENGINE'] != 'vagrant',
        'Skipping vagrant tests...')
    def test_vagrant_write_vagrantfile(self):
        self.runner.vagrant_write_vagrantfile('/tmp/test_folder/test_vm')
        required_content = """
        Vagrant.configure("2") do |config|
            config.vm.box = "ailispaw/barge"
            config.vm.synced_folder "{}", "{}"
            config.vm.synced_folder "/tmp/test_folder", "/tmp/test_folder"
        end
        """.format(os.environ['HOME'], os.environ['HOME'])
        f = open('/tmp/test_folder/test_vm/Vagrantfile')
        content = f.readlines()
        f.close()
        for line in content:
            self.assertEqual(line in required_content, True)


class TestHostRunner(unittest.TestCase):

    def setUp(self):
        warnings.filterwarnings(action="ignore", message="unclosed",
                                category=ResourceWarning)
        os.makedirs('/tmp/test_folder', exist_ok=True)
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
        self.wf = HCLWorkflow('/tmp/test_folder/a.workflow')
        self.wf.parse()
        WorkflowRunner.instantiate_runners(
            'docker', self.wf, '/tmp/test_folder', False, False, '12345')

    def tearDown(self):
        os.chdir('/tmp')
        shutil.rmtree('/tmp/test_folder')
        log.setLevel('NOTSET')

    def test_run(self):
        runner = self.wf.step['sample action']['runner']
        self.assertRaises(SystemExit, runner.run, reuse=True)
        runner.run()

    def test_host_prepare(self):
        runner = self.wf.step['sample action']['runner']
        runner.step['runs'] = ['script1']
        runner.step['args'] = ['github.com']
        cmd = runner.host_prepare()
        self.assertEqual(cmd, ['/tmp/test_folder/script1', 'github.com'])
        os.makedirs('/tmp/test_folder/action/myaction', exist_ok=True)
        runner.step['uses'] = './action/myaction'
        runner.step['runs'] = ['script']
        runner.step['args'] = ['arg1', 'arg2']
        cmd = runner.host_prepare()
        self.assertEqual(
            cmd, [
                '/tmp/test_folder/./action/myaction/./script', 'arg1', 'arg2'])
        os.chdir('/tmp/test_folder')
        runner.step.pop('runs')
        cmd = runner.host_prepare()
        self.assertEqual(
            cmd, [
                '/tmp/test_folder/./action/myaction/./entrypoint.sh',
                'arg1', 'arg2'])

    def test_host_start(self):
        runner = self.wf.step['sample action']['runner']
        e = runner.host_start([
            "sh", "-c", "echo 'Hello from Popper 2.x !' > popper.file"
        ])
        self.assertEqual(e, 0)
        self.assertEqual(os.path.exists('popper.file'), True)


class TestConcurrentExecution(unittest.TestCase):

    def setUp(self):
        warnings.filterwarnings(action="ignore", message="unclosed",
                                category=ResourceWarning)
        os.makedirs('/tmp/test_folder/gha-demo', exist_ok=True)
        # log.setLevel('CRITICAL')
        git.Repo.clone_from(
            'https://github.com/JayjeetAtGithub/popper-scaffold-workflow',
            '/tmp/test_folder/gha-demo')
        os.chdir('/tmp/test_folder/gha-demo')
        self.wf_one = HCLWorkflow('/tmp/test_folder/gha-demo/main.workflow')
        self.wf_two = HCLWorkflow('/tmp/test_folder/gha-demo/main.workflow')
        self.wf_three = HCLWorkflow('/tmp/test_folder/gha-demo/main.workflow')
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
                False, False, False, False, os.environ['ENGINE'])
        with ThreadPoolExecutor(max_workers=mp.cpu_count()) as ex:
            ex.submit(self.runner_one.run, *args)
            ex.submit(self.runner_two.run, *args)
            ex.submit(self.runner_three.run, *args)
