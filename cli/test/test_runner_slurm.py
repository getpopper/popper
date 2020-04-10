import os
import unittest
import tempfile
import utils as testutils

from popper.config import PopperConfig
from popper.runner import WorkflowRunner
from popper.parser import YMLWorkflow
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
        self.assertEqual(
            self.slurm_runner._tail_output('slurm-x.out'), 0)
        self.assertEqual(len(self.slurm_runner._out_stream_pid), 1)

    def test_stop_running_tasks(self):
        self.Popen.set_command('scancel --name job_a', returncode=0)
        self.slurm_runner._spawned_jobs.add('job_a')
        # If no exception is raised, implies scancel was called and
        # got caught in mock Popen.
        self.slurm_runner.stop_running_tasks()

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
        repo = testutils.mk_repo()
        conf = PopperConfig(
            engine_name='docker',
            resman_name='slurm',
            dry_run=True,
            workspace_dir=repo.working_dir)

        with WorkflowRunner(conf) as r:
            wf = YMLWorkflow("""
            version: '1'
            steps:
            - uses: 'popperized/bin/sh@master'
              runs: [cat]
              args: README.md
            """)
            wf.parse()
            # If not exception raised, that means dry-run worked and
            # submit_batch_job was not called.
            r.run(wf)


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

        repo = testutils.mk_repo().working_dir
        config_file = os.path.join(repo, 'settings.yml')
        with open(config_file, 'w') as f:
            f.write("""
            engine:
              name: docker
              options:
                privileged: True
                hostname: popper.local
                domainname: www.example.org
                volumes: ["/path/in/host:/path/in/container"]
                environment:
                  FOO: bar
            resource_manager:
              name: slurm
            """)

        conf = {'workspace_dir': '/w', 'config_file': config_file}
        with DockerRunner(config=PopperConfig(**conf)) as drunner:
            step = {'args': ['-two', '-flags']}
            cmd = drunner._create_cmd(step, 'foo:1.9', 'container_name')

            expected = ('docker create --name container_name '
                        '--workdir /workspace '
                        '-v /w:/workspace '
                        '-v /var/run/docker.sock:/var/run/docker.sock '
                        '-v /path/in/host:/path/in/container '
                        '-e FOO=bar --privileged --hostname popper.local '
                        '--domainname www.example.org '
                        'foo:1.9 -two -flags')

            self.assertEqual(expected, cmd)


    def test_run(self):
        # TODO: create a mock for Popen; create a workflow object and then
        # instantiate a WorkflowRunner. Then invoke WorkflowRunner.run() and
        # check that:
        # - submit_job generates a script containing the right docker commands
        # - sbatch and tail commands get invoked with the right flags
        pass
