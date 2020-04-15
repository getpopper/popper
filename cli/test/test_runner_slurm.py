import os
import unittest

from popper.config import PopperConfig
from popper.runner_slurm import SlurmRunner, DockerRunner
from popper.cli import log as log

from dotmap import DotMap

from popper_test import PopperTest
from testfixtures import Replacer
from testfixtures.popen import MockPopen


FIXDIR = f'{os.path.dirname(os.path.realpath(__file__))}/fixtures'


def _wfile(name, format):
    return f'{FIXDIR}/{name}.{format}'


class TestSlurmSlurmRunner(unittest.TestCase, PopperTest):
    def setUp(self):
        log.setLevel('CRITICAL')
        self.Popen = MockPopen()
        replacer = Replacer()
        replacer.replace('popper.utils.Popen', self.Popen)
        self.addCleanup(replacer.restore)
        self.repo = self.mk_repo().working_dir
        self.slurm_runner = SlurmRunner(DotMap({}))

    def tearDown(self):
        log.setLevel('NOTSET')

    def test__stream_output(self):
        self.Popen.set_command('tail -f slurm-x.out', returncode=0)
        self.slurm_runner._stream_output('slurm-x.out')

    def test__stream_error(self):
        self.Popen.set_command('tail -f slurm-x.err', returncode=0)
        self.slurm_runner._stream_error('slurm-x.err')

    def test_generate_script(self):
        cmd = " ".join(["docker", "version"])
        job_script = os.path.join(self.repo, 'script.sh')
        SlurmRunner.generate_script(cmd, 'sample_job', job_script)
        with open(job_script, 'r') as f:
            content = f.read()
        self.assertEqual(content, "#!/bin/bash\ndocker version")

    def test_touch_log_files(self):
        out_file = os.path.join(self.repo, 'slurm-x.out')
        err_file = os.path.join(self.repo, 'slurm-x.err')
        self.slurm_runner.touch_log_files(out_file, err_file)
        self.assertEqual(os.path.exists(out_file), True)
        self.assertEqual(os.path.exists(err_file), True)

    def test_cancel_job(self):
        self.Popen.set_command('scancel --name job_a', returncode=0)
        SlurmRunner.spawned_jobs.add('job_a')
        SlurmRunner.cancel_job()


class TestSlurmDockerRunner(unittest.TestCase):
    def setUp(self):
        log.setLevel('CRITICAL')
        self.test_dir = "/path/to/workspace"
        common_kwargs = {
            'skip_clone': False,
            'skip_pull': False,
            'dry_run': False,
            'workspace_dir': self.test_dir,
            'quiet': False,
            'reuse': False,
            'engine_options': dict(),
            'resman_options': dict()}

        self.config = PopperConfig(
            config_file=_wfile("settings_3", "yml"),
            engine=None,
            resource_manager=None,
            **common_kwargs)

        self.docker_runner = DockerRunner(self.config)
        self.cls = TestSlurmDockerRunner

    @classmethod
    def setUpClass(cls):
        cls.step = {'cmd_list': [], 'name': 'one'}

    def tearDown(self):
        log.setLevel('NOTSET')

    def test_docker_build(self):
        DockerRunner.docker_build(
            self.cls.step,
            'alpine',
            '/path/to/build_dir',
            self.config.dry_run)
        self.assertEqual(
            self.cls.step['cmd_list'],
            ['docker build alpine /path/to/build_dir > /dev/null'])

    def test_docker_create(self):
        DockerRunner.docker_create(self.cls.step, 'alpine', 'c1', self.config)
        self.assertEqual(self.cls.step['cmd_list'], [
            'docker build alpine /path/to/build_dir > /dev/null',
            'docker create --name c1 --workdir /workspace -v /path/to/workspace:/workspace -v /var/run/docker.sock:/var/run/docker.sock alpine   > /dev/null'])

    def test_docker_pull(self):
        DockerRunner.docker_pull(self.cls.step, 'alpine', self.config.dry_run)
        self.assertEqual(self.cls.step['cmd_list'], [
            'docker build alpine /path/to/build_dir > /dev/null',
            'docker create --name c1 --workdir /workspace -v /path/to/workspace:/workspace -v /var/run/docker.sock:/var/run/docker.sock alpine   > /dev/null',
            'docker pull alpine > /dev/null'])

    def test_docker_rm(self):
        DockerRunner.docker_rm(self.step, 'c1', self.config.dry_run)
        self.assertEqual(self.cls.step['cmd_list'], [
            'docker build alpine /path/to/build_dir > /dev/null',
            'docker create --name c1 --workdir /workspace -v /path/to/workspace:/workspace -v /var/run/docker.sock:/var/run/docker.sock alpine   > /dev/null',
            'docker pull alpine > /dev/null',
            'docker rm -f c1 || true > /dev/null'])

    def test_docker_start(self):
        DockerRunner.docker_start(self.step, 'c1', self.config.dry_run)
        self.assertEqual(self.cls.step['cmd_list'], [
            'docker build alpine /path/to/build_dir > /dev/null',
            'docker create --name c1 --workdir /workspace -v /path/to/workspace:/workspace -v /var/run/docker.sock:/var/run/docker.sock alpine   > /dev/null',
            'docker pull alpine > /dev/null',
            'docker rm -f c1 || true > /dev/null',
            'docker start --attach c1'])
