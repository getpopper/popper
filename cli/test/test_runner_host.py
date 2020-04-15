import os
import time
import unittest

from subprocess import Popen

import psutil
import docker

import utils as testutils
import popper.utils as pu

from testfixtures import LogCapture

from popper.config import PopperConfig
from popper.parser import YMLWorkflow
from popper.runner import WorkflowRunner
from popper.runner_host import HostRunner, DockerRunner
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
        cmd = ["echo", "hello-world"]
        pid, ecode, output = HostRunner._exec_cmd(cmd, logging=False)
        self.assertGreater(pid, 0)
        self.assertEqual(ecode, 0)
        self.assertEqual(output, "hello-world\n")

        with LogCapture('popper') as log:
            pid, ecode, output = HostRunner._exec_cmd(cmd)
            self.assertGreater(pid, 0)
            self.assertEqual(ecode, 0)
            self.assertEqual(output, "")
            log.check_present(('popper', 'STEP_INFO', 'hello-world\n'))

        cmd = ["env"]
        pid, ecode, output = HostRunner._exec_cmd(
            cmd, env={'TESTACION': 'test'}, cwd="/tmp", logging=False)
        self.assertGreater(pid, 0)
        self.assertEqual(ecode, 0)
        self.assertTrue('TESTACION' in output)

        _pids = set()
        _, _, _ = HostRunner._exec_cmd(["sleep", "2"], pids=_pids)
        self.assertEqual(len(_pids), 1)

    def test_stop_running_tasks(self):
        pid = Popen(["sleep", "2000"]).pid
        with HostRunner() as hr:
            hr._spawned_pids.add(pid)
            hr.stop_running_tasks()
        time.sleep(2)
        proc = psutil.Process(pid)
        self.assertEqual(proc.status(), psutil.STATUS_ZOMBIE)


class TestHostDockerRunner(unittest.TestCase):
    def setUp(self):
        log.setLevel('CRITICAL')

    @unittest.skipIf(os.environ['ENGINE'] != 'docker', 'ENGINE != docker')
    def test_create_container(self):
        config = PopperConfig()
        step = {
            'uses': 'docker://alpine:3.9',
            'runs': ['echo hello'],
            'name': 'kontainer_one'
        }
        cid = pu.sanitized_name(step['name'], config.wid)
        with DockerRunner(init_docker_client=True, config=config) as dr:
            c = dr._create_container(cid, step)
            self.assertEqual(c.status, 'created')
            c.remove()

    @unittest.skipIf(os.environ['ENGINE'] != 'docker', 'ENGINE != docker')
    def test_stop_running_tasks(self):
        with DockerRunner() as dr:
            dclient = docker.from_env()
            c1 = dclient.containers.run(
                'debian:buster-slim', 'sleep 20000', detach=True)
            c2 = dclient.containers.run(
                'alpine:3.9', 'sleep 10000', detach=True)
            dr._spawned_containers.add(c1)
            dr._spawned_containers.add(c2)
            dr.stop_running_tasks()
            self.assertEqual(c1.status, 'created')
            self.assertEqual(c2.status, 'created')
            dclient.close()

    @unittest.skipIf(os.environ['ENGINE'] != 'docker', 'ENGINE != docker')
    def test_get_container_kwargs(self):
        step = {
            'uses': 'popperized/bin/sh@master',
            'args': ['ls'],
            'name': 'one',
            'repo_dir': '/path/to/repo/dir',
            'step_dir': 'sh'}

        config_dict = {
            'engine': {
                'name': 'docker',
                'options': {
                    'privileged': True,
                    'hostname': 'popper.local',
                    'domainname': 'www.example.org',
                    'volumes': ['/path/in/host:/path/in/container'],
                    'environment': {'FOO': 'bar'}
                }
            },
            'resource_manager': {
                'name': 'slurm'
            }
        }

        config = PopperConfig(
            config_file=config_dict,
            workspace_dir='/path/to/workdir')

        with DockerRunner(init_docker_client=False, config=config) as dr:
            args = dr._get_container_kwargs(
                step, 'alpine:3.9', 'container_a')

            self.assertEqual(args, {
                'image': 'alpine:3.9',
                'command': ['ls'],
                'name': 'container_a',
                'volumes': [
                    '/path/to/workdir:/workspace',
                    '/var/run/docker.sock:/var/run/docker.sock',
                    '/path/in/host:/path/in/container'],
                'working_dir': '/workspace',
                'environment': {'FOO': 'bar'},
                'entrypoint': None,
                'detach': True,
                'privileged': True,
                'hostname': 'popper.local',
                'domainname': 'www.example.org'})

    @unittest.skipIf(os.environ['ENGINE'] != 'docker', 'ENGINE != docker')
    def test_get_build_info(self):
        step = {
            'uses': 'popperized/bin/sh@master',
            'args': ['ls'],
            'name': 'one',
            'repo_dir': '/path/to/repo/dir',
            'step_dir': 'sh'}
        with DockerRunner(init_docker_client=False) as dr:
            build, img, tag, build_sources = dr._get_build_info(step)
            self.assertEqual(build, True)
            self.assertEqual(img, 'popperized/bin')
            self.assertEqual(tag, 'master')
            self.assertEqual(
                build_sources,
                '/path/to/repo/dir/sh')

            step = {
                'uses': 'docker://alpine:3.9',
                'runs': ['sh', '-c', 'echo $FOO > hello.txt ; pwd'],
                'env': {'FOO': 'bar'},
                'name': '1'
            }

        with DockerRunner(init_docker_client=False) as dr:
            build, img, tag, build_sources = dr._get_build_info(step)
            self.assertEqual(build, False)
            self.assertEqual(img, 'alpine')
            self.assertEqual(tag, '3.9')
            self.assertEqual(build_sources, None)

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
