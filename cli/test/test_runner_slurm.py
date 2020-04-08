import unittest
import tempfile

from popper.config import PopperConfig
from popper.runner_slurm import SlurmRunner, DockerRunner
from popper.cli import log as log

from testfixtures import Replacer
from testfixtures.popen import MockPopen


class TestSlurmSlurmRunner(unittest.TestCase):
    def setUp(self):
        log.setLevel('CRITICAL')
        self.Popen = MockPopen()
        replacer = Replacer()
        replacer.replace('popper.runner_host.Popen', self.Popen)
        self.addCleanup(replacer.restore)
        self.repo = tempfile.mkdtemp()
        self.slurm_runner = SlurmRunner(config=PopperConfig())

    def tearDown(self):
        log.setLevel('NOTSET')

    def test_tail_output(self):
        self.Popen.set_command('tail -f slurm-x.out', returncode=0)
        self.slurm_runner._tail_output('slurm-x.out')
        # TODO: assert that tail was invoked

    def test_stop_running_tasks(self):
        self.Popen.set_command('scancel --name job_a', returncode=0)
        self.slurm_runner._spawned_jobs.add('job_a')
        self.slurm_runner.stop_running_tasks()
        # TODO: assert that scancel was invoked

    def test_submit_job(self):
        # TODO:
        # - assert that sbatch gets invoked with the right parameters
        # - assert that when command is given (e.g. ['ls', '-la']) the
        #   generated script contains it
        # - assert that Popen is invoked twice, one for sbatch and another for
        #   the tail command
        # - assert that stream thread is not running
        # - assert that job is properly removed from list of spawned jobs
        #
        # NOTE: the above might be broken in multiple tests
        pass

    def test_submit_job_failure(self):
        # TODO:
        # - test that when a _submit_batch_job fails, a non-zero exit error
        #   code is returned
        pass

    def test_dry_run(self):
        # TODO: assert that when dry_run=True, submit_job is not invoked
        pass


class TestSlurmDockerRunner(unittest.TestCase):
    def setUp(self):
        log.setLevel('CRITICAL')

    def tearDown(self):
        log.setLevel('NOTSET')

    def test_create_cmd(self):
        conf = {'workspace_dir': '/w'}
        with DockerRunner(config=PopperConfig(**conf)) as drunner:
            step = {'args': ['-two', '-flags']}
            cmd = drunner._create_cmd(step, 'foo:1.9', 'container_name')

            expected = (
                'docker create'
                ' --name container_name'
                ' --workdir /workspace'
                ' -v /w:/workspace'
                ' -v /var/run/docker.sock:/var/run/docker.sock'
                ' foo:1.9 -two -flags')

            self.assertEqual(expected, cmd)

        # TODO: test many times the above, but with distinct contents for step

    def test_run(self):
        # TODO: create a mock for Popen; create a workflow object and then
        # instantiate a WorkflowRunner. Then invoke WorkflowRunner.run() and
        # check that:
        # - submit_job generates a script containing the right docker commands
        # - sbatch and tail commands get invoked with the right flags
        pass
