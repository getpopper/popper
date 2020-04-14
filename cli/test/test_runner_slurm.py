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

    def tearDown(self):
        log.setLevel('NOTSET')

    def test_tail_output(self):
        self.Popen.set_command('tail -f slurm-x.out', returncode=0)
        with SlurmRunner(config=PopperConfig()) as sr:
            self.assertEqual(
                sr._tail_output('slurm-x.out'), 0)
            self.assertEqual(
                len(sr._out_stream_pid), 1)

    def test_stop_running_tasks(self):
        self.Popen.set_command('scancel --name job_a', returncode=0)
        with SlurmRunner(config=PopperConfig()) as sr:
            sr._spawned_jobs.add('job_a')
            sr.stop_running_tasks()
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
        with SlurmRunner(config=config) as sr:
            sr._submit_batch_job(["ls -la"], step)
            with open("/tmp/popper/slurm/popper_sample_123abc.sh", 'r') as f:
                content = f.read()

            self.assertEqual(content, "#!/bin/bash\nls -la")
            self.assertEqual(len(sr._spawned_jobs), 0)
            self.assertEqual(sr._out_stream_thread.is_alive(), False)

        call_tail = call.Popen(
            ['tail', '-f', '/tmp/popper/slurm/popper_sample_123abc.out'],
            cwd=os.getcwd(),
            env=None, preexec_fn=os.setsid,
            stderr=-2, stdout=-1, universal_newlines=True)

        call_sbatch = call.Popen(
            ['sbatch', '--wait', '--job-name',
            'popper_sample_123abc', '--output',
            '/tmp/popper/slurm/popper_sample_123abc.out',
            '/tmp/popper/slurm/popper_sample_123abc.sh'],
            cwd=os.getcwd(), env=None,
            preexec_fn=os.setsid,
            stderr=-2, stdout=-1, universal_newlines=True)

        self.assertEqual(call_tail in self.Popen.all_calls, True)
        self.assertEqual(call_sbatch in self.Popen.all_calls, True)

    @replace('popper.runner_slurm.os.kill', mock_kill)
    def test_submit_job_failure(self, mock_kill):
        self.Popen.set_command(
            'sbatch --wait --job-name popper_1_123abc '
            '--output /tmp/popper/slurm/popper_1_123abc.out '
            '/tmp/popper/slurm/popper_1_123abc.sh', returncode=12)

        self.Popen.set_command(
            'tail -f /tmp/popper/slurm/popper_1_123abc.out',
            returncode=0)

        config_dict = {
            'engine': {
                'name': 'docker',
                'options': {}
            },
            'resource_manager': {
                'name': 'slurm',
                'options': {}
            }
        }

        config = PopperConfig(
            workspace_dir='/w',
            config_file=config_dict)
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
                cwd=os.getcwd(),
                env=None, preexec_fn=os.setsid,
                stderr=-2, stdout=-1, universal_newlines=True)

            call_sbatch = call.Popen(['sbatch',
                                      '--wait',
                                      '--job-name',
                                      'popper_1_123abc',
                                      '--output',
                                      '/tmp/popper/slurm/popper_1_123abc.out',
                                      '/tmp/popper/slurm/popper_1_123abc.sh'],
                                     cwd=os.getcwd(),
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

        config = {'workspace_dir': '/w', 'config_file': config_dict}
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
            workspace_dir='/w',
            config_file=config_dict)
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
