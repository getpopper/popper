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
        replacer.replace('popper.utils.Popen', self.Popen)
        self.addCleanup(replacer.restore)
        self.repo = testutils.mk_repo().working_dir

    def test__stream_output(self):
        self.Popen.set_command('tail -f slurm-x.out', returncode=0)
        slurm_runner = SlurmRunner(DotMap({}))
        self.assertEqual(slurm_runner._stream_output('slurm-x.out'), 0)

    def test_generate_script(self):
        cmd = " ".join(["docker", "version"])
        job_script = os.path.join(self.repo, 'script.sh')
        SlurmRunner.generate_script(cmd, 'sample_job', job_script)

        with open(job_script, 'r') as f:
            content = f.read()

    def test_touch_log_files(self):
        out_file = os.path.join(self.repo, 'slurm-x.out')
        err_file = os.path.join(self.repo, 'slurm-x.err')
        slurm_runner = SlurmRunner(DotMap({}))
        slurm_runner.touch_log_files(out_file, err_file)

        self.assertEqual(os.path.exists(out_file), True)
        self.assertEqual(os.path.exists(err_file), True)

    def test_cancel_job(self):
        self.Popen.set_command('scancel --name job_a', returncode=0)
        slurm_runner = SlurmRunner(DotMap({}))
        SlurmRunner.spawned_jobs.add('job_a')
        SlurmRunner.cancel_job()


# class TestSlurmDockerRunner(unittest.TestCase):
#     def setUp(self):
#         log.setLevel('CRITICAL')
#         self.Popen = MockPopen()
#         replacer = Replacer()
#         replacer.replace('popper.utils.Popen', self.Popen)
#         self.addCleanup(replacer.restore)

#     def test_start_container(self):
#         self.Popen.set_command('srun docker start --attach', returncode=0)
#         config = DotMap()
#         config.workspace_dir = os.environ["HOME"]
#         docker_runner = DockerRunner(config)
#         self.assertEqual(docker_runner.exec_srun_cmd(
#             ['docker', 'start', '--attach']), 0)
#         self.assertEqual(len(SlurmRunner.spawned_processes), 0)
