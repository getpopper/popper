import os
import unittest

import utils as testutils

from popper.parser import YMLWorkflow
from popper.runner import WorkflowRunner
from popper.runner_slurm import SlurmRunner, DockerRunner
from popper.cli import log as log

from dotmap import DotMap

from testfixtures.mock import call
from testfixtures import Replacer, ShouldRaise, compare
from testfixtures.popen import MockPopen, PopenBehaviour


class TestSlurmSlurmRunner(unittest.TestCase):
    def setUp(self):
        log.setLevel('CRITICAL')
        self.Popen = MockPopen()
        replacer = Replacer()
        replacer.replace('popper.runner_slurm.Popen', self.Popen)
        self.addCleanup(replacer.restore)

    def test_exec_run(self):
        self.Popen.set_command('srun ls -l', returncode=0)
        config = DotMap()
        config.workspace_dir = os.environ["HOME"]
        slurm_runner = SlurmRunner(config)
        self.assertEqual(slurm_runner.exec_srun_cmd(['ls', '-l']), 0)
        self.assertEqual(len(SlurmRunner.spawned_processes), 0)


class TestSlurmDockerRunner(unittest.TestCase):
    def setUp(self):
        log.setLevel('CRITICAL')
        self.Popen = MockPopen()
        replacer = Replacer()
        replacer.replace('popper.runner_slurm.Popen', self.Popen)
        self.addCleanup(replacer.restore)

    def test_start_container(self):
        self.Popen.set_command('srun docker start --attach', returncode=0)
        config = DotMap()
        config.workspace_dir = os.environ["HOME"]
        docker_runner = DockerRunner(config)
        self.assertEqual(docker_runner.exec_srun_cmd(
            ['docker', 'start', '--attach']), 0)
        self.assertEqual(len(SlurmRunner.spawned_processes), 0)
