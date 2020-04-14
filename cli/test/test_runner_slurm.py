import os
import unittest
import tempfile
import utils as testutils

from popper.config import PopperConfig
from popper.runner import WorkflowRunner
from popper.parser import YMLWorkflow
from popper.runner_slurm import SlurmRunner, DockerRunner
from popper.cli import log as log

from testfixtures import Replacer, replace, compare
from testfixtures.popen import MockPopen
from testfixtures.mock import call


def mock_kill(pid, sig):
    return 0


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
        self.slurm_runner.stop_running_tasks()
        self.assertEqual(
            call.Popen(
                ['scancel', '--name', 'job_a'],
                cwd=os.getcwd(),
                env=None, preexec_fn=os.setsid, stderr=-2, stdout=-1,
                universal_newlines=True) in self.Popen.all_calls, True)

    @replace('popper.runner_slurm.os.kill', mock_kill)
    def test_submit_batch_job(self, mock_kill):
        self.Popen.set_command(
            'sbatch --wait '
            '--job-name popper_sample_123abc '
            '--output /tmp/popper/slurm/popper_sample_123abc.out '
            '/tmp/popper/slurm/popper_sample_123abc.sh',
            returncode=0)
        self.Popen.set_command(
            'tail -f /tmp/popper/slurm/popper_sample_123abc.out', returncode=0)
        config = PopperConfig(workspace_dir='/w')
        config.wid = "123abc"
        step = {"name": "sample"}
        slurm_runner = SlurmRunner(config=config)
        slurm_runner._submit_batch_job(["ls -la"], step)
        with open("/tmp/popper/slurm/popper_sample_123abc.sh", 'r') as f:
            content = f.read()

        self.assertEqual(content, "#!/bin/bash\nls -la")
        self.assertEqual(len(slurm_runner._spawned_jobs), 0)
        self.assertEqual(slurm_runner._out_stream_thread.is_alive(), False)

    @replace('popper.runner_slurm.os.kill', mock_kill)
    def test_submit_job_failure(self, mock_kill):
        self.Popen.set_command(
            'sbatch --wait --job-name popper_1_123abc '
            '--output /tmp/popper/slurm/popper_1_123abc.out '
            '/tmp/popper/slurm/popper_1_123abc.sh', returncode=12)

        self.Popen.set_command(
            'tail -f /tmp/popper/slurm/popper_1_123abc.out',
            returncode=0)
        repo = testutils.mk_repo().working_dir
        config_file = os.path.join(repo, 'settings.yml')
        with open(config_file, 'w') as f:
            f.write("""
            engine:
              name: docker
            resource_manager:
              name: slurm
            """)

        config = PopperConfig(
            workspace_dir='/w',
            config_file=config_file)
        config.wid = "123abc"

        with WorkflowRunner(config) as r:
            wf = YMLWorkflow("""
            version: '1'
            steps:
            - uses: 'popperized/bin/sh@master'
              runs: [cat]
              args: README.md
            """)
            wf.parse()
            self.assertRaises(SystemExit, r.run, wf)

            call_tail = call.Popen(
                ['tail', '-f', '/tmp/popper/slurm/popper_1_123abc.out'],
                cwd=f'{os.environ["HOME"]}/popper/cli/test',
                env=None, preexec_fn=os.setsid,
                stderr=-2, stdout=-1, universal_newlines=True)

            call_sbatch = call.Popen(['sbatch',
                                      '--wait',
                                      '--job-name',
                                      'popper_1_123abc',
                                      '--output',
                                      '/tmp/popper/slurm/popper_1_123abc.out',
                                      '/tmp/popper/slurm/popper_1_123abc.sh'],
                                     cwd=f'{os.environ["HOME"]}/popper/cli/test',
                                     env=None,
                                     preexec_fn=os.setsid,
                                     stderr=-2,
                                     stdout=-1,
                                     universal_newlines=True)

            self.assertEqual(call_tail in self.Popen.all_calls, True)
            self.assertEqual(call_sbatch in self.Popen.all_calls, True)

    def test_dry_run(self):
        repo = testutils.mk_repo()
        config = PopperConfig(
            engine_name='docker',
            resman_name='slurm',
            dry_run=True,
            workspace_dir=repo.working_dir)

        with WorkflowRunner(config) as r:
            wf = YMLWorkflow("""
            version: '1'
            steps:
            - uses: 'popperized/bin/sh@master'
              runs: [cat]
              args: README.md
            """)
            wf.parse()
            r.run(wf)

        self.assertEqual(self.Popen.all_calls, [])


class TestSlurmDockerRunner(unittest.TestCase):
    def setUp(self):
        log.setLevel('CRITICAL')
        self.Popen = MockPopen()
        replacer = Replacer()
        replacer.replace('popper.runner_host.Popen', self.Popen)
        self.addCleanup(replacer.restore)

    def tearDown(self):
        log.setLevel('NOTSET')

    def test_create_cmd(self):
        config = {'workspace_dir': '/w'}
        with DockerRunner(config=PopperConfig(**config)) as drunner:
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

        config = {'workspace_dir': '/w', 'config_file': config_file}
        with DockerRunner(config=PopperConfig(**config)) as drunner:
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

    @replace('popper.runner_slurm.os.kill', mock_kill)
    def test_run(self, mock_kill):
        self.Popen.set_command(
            'sbatch --wait --job-name popper_1_123abc '
            '--output /tmp/popper/slurm/popper_1_123abc.out '
            '/tmp/popper/slurm/popper_1_123abc.sh', returncode=0)

        self.Popen.set_command(
            'tail -f /tmp/popper/slurm/popper_1_123abc.out',
            returncode=0)
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

        config = PopperConfig(
            workspace_dir='/w',
            config_file=config_file)
        config.wid = "123abc"

        with WorkflowRunner(config) as r:
            wf = YMLWorkflow("""
            version: '1'
            steps:
            - uses: 'popperized/bin/sh@master'
              runs: [cat]
              args: README.md
            """)
            wf.parse()
            r.run(wf)

        with open('/tmp/popper/slurm/popper_1_123abc.sh', 'r') as f:
            content = f.read()
            self.assertEqual(content,
                             f"""#!/bin/bash
docker rm -f popper_1_123abc || true
docker build -t popperized/bin:master {os.environ['HOME']}/.cache/popper/123abc/github.com/popperized/bin/sh
docker create --name popper_1_123abc --workdir /workspace --entrypoint cat -v /w:/workspace -v /var/run/docker.sock:/var/run/docker.sock -v /path/in/host:/path/in/container -e FOO=bar --privileged --hostname popper.local --domainname www.example.org popperized/bin:master README.md
docker start --attach popper_1_123abc""")
