import os
import unittest
import tempfile

from testfixtures import compare, Replacer, replace
from testfixtures.popen import MockPopen
from testfixtures.mock import call

from popper.config import ConfigLoader
from popper.runner import WorkflowRunner
from popper.parser import WorkflowParser
from popper.runner_slurm import (
    SlurmRunner,
    DockerRunner,
    SingularityRunner,
    PodmanRunner,
)
from popper.cli import log as log

from .test_common import PopperTest

from box import Box


config = ConfigLoader.load(workspace_dir="/w")


def mock_kill(pid, sig):
    return 0


class TestSlurmSlurmRunner(PopperTest):
    def setUp(self):
        log.setLevel("CRITICAL")
        self.Popen = MockPopen()
        replacer = Replacer()
        replacer.replace("popper.runner_host.Popen", self.Popen)
        self.addCleanup(replacer.restore)

    def tearDown(self):
        log.setLevel("NOTSET")

    def test_tail_output(self):
        self.Popen.set_command("tail -f slurm-x.out", returncode=0)
        with SlurmRunner(config=ConfigLoader.load()) as sr:
            self.assertEqual(sr._tail_output("slurm-x.out"), 0)
            self.assertEqual(len(sr._out_stream_pid), 1)

    def test_stop_running_tasks(self):
        self.Popen.set_command("scancel --name job_a", returncode=0)
        with SlurmRunner(config=ConfigLoader.load()) as sr:
            sr._spawned_jobs.add("job_a")
            sr.stop_running_tasks()
            compare(
                call.Popen(
                    ["scancel", "--name", "job_a"],
                    cwd=os.getcwd(),
                    env=None,
                    preexec_fn=os.setsid,
                    stderr=-2,
                    stdout=-1,
                    universal_newlines=True,
                ),
                self.Popen.all_calls[0],
            )

    @replace("popper.runner_slurm.os.kill", mock_kill)
    def test_exec_srun(self, mock_kill):
        config = ConfigLoader.load(workspace_dir="/w")
        self.Popen.set_command(
            "srun --nodes 1 --ntasks 1 --ntasks-per-node 1 ls -la", returncode=0,
        )
        step = Box({"id": "sample"}, default_box=True)
        with SlurmRunner(config=config) as sr:
            e = sr._exec_srun(["ls", "-la"], step, logging=True)
            self.assertEqual(e, 0)

        call_srun = call.Popen(
            [
                "srun",
                "--nodes",
                "1",
                "--ntasks",
                "1",
                "--ntasks-per-node",
                "1",
                "ls",
                "-la",
            ],
            cwd=os.getcwd(),
            env=None,
            preexec_fn=os.setsid,
            stderr=-2,
            stdout=-1,
            universal_newlines=True,
        )

        self.assertEqual(call_srun in self.Popen.all_calls, True)

    @replace("popper.runner_slurm.os.kill", mock_kill)
    def test_exec_mpi(self, mock_kill):
        config = ConfigLoader.load(workspace_dir="/w")
        self.Popen.set_command(
            "sbatch "
            f"--job-name popper_sample_{config.wid} "
            "--wait "
            f"--output popper_sample_{config.wid}.out "
            f"popper_sample_{config.wid}.sh",
            returncode=0,
        )
        self.Popen.set_command(f"tail -f popper_sample_{config.wid}.out", returncode=0)
        step = Box({"id": "sample"}, default_box=True)
        with SlurmRunner(config=config) as sr:
            e = sr._exec_mpi(["ls -la"], step)
            self.assertEqual(e, 0)
            with open(f"popper_sample_{config.wid}.sh", "r") as f:
                content = f.read()

            self.assertEqual(
                content,
                """#!/bin/bash
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --ntasks-per-node=1
mpirun ls -la""",
            )
            self.assertEqual(len(sr._spawned_jobs), 0)
            self.assertEqual(sr._out_stream_thread.is_alive(), False)

        call_tail = call.Popen(
            ["tail", "-f", f"popper_sample_{config.wid}.out"],
            cwd=os.getcwd(),
            env=None,
            preexec_fn=os.setsid,
            stderr=-2,
            stdout=-1,
            universal_newlines=True,
        )

        call_sbatch = call.Popen(
            [
                "sbatch",
                "--job-name",
                f"popper_sample_{config.wid}",
                "--wait",
                "--output",
                f"popper_sample_{config.wid}.out",
                f"popper_sample_{config.wid}.sh",
            ],
            cwd=os.getcwd(),
            env=None,
            preexec_fn=os.setsid,
            stderr=-2,
            stdout=-1,
            universal_newlines=True,
        )

        self.assertEqual(call_tail in self.Popen.all_calls, True)
        self.assertEqual(call_sbatch in self.Popen.all_calls, True)

    def test_dry_run(self):
        config = ConfigLoader.load(
            engine_name="docker", resman_name="slurm", dry_run=True,
        )

        with WorkflowRunner(config) as r:
            wf_data = {
                "steps": [
                    {
                        "uses": "popperized/bin/sh@master",
                        "runs": ["cat"],
                        "args": ["README.md"],
                    }
                ]
            }
            r.run(WorkflowParser.parse(wf_data=wf_data))

        self.assertEqual(self.Popen.all_calls, [])

    @replace("popper.runner_slurm.os.kill", mock_kill)
    def test_exec_srun_failure(self, mock_kill):
        config_dict = {
            "engine": {
                "name": "podman",
                "options": {
                    "privileged": True,
                    "hostname": "popper.local",
                    "domainname": "www.example.org",
                    "volumes": ["/path/in/host:/path/in/container"],
                    "environment": {"FOO": "bar"},
                },
            },
            "resource_manager": {
                "name": "slurm",
                "options": {"1": {"nodes": 2, "nodelist": "worker1,worker2"}},
            },
        }

        config = ConfigLoader.load(workspace_dir="/w", config_file=config_dict)

        self.Popen.set_command(
            f"srun --nodes 2 --ntasks 2 --ntasks-per-node 1 --nodelist worker1,worker2 podman rm -f popper_1_{config.wid}",
            returncode=0,
        )

        self.Popen.set_command(
            f"srun --nodes 2 --ntasks 2 --ntasks-per-node 1 --nodelist worker1,worker2 podman pull alpine:latest",
            returncode=0,
        )

        self.Popen.set_command(
            f"srun --nodes 2 --ntasks 2 --ntasks-per-node 1 --nodelist worker1,worker2 podman create --name popper_1_{config.wid} --workdir /workspace -v /w:/workspace:Z -v /path/in/host:/path/in/container -e FOO=bar --privileged --hostname popper.local --domainname www.example.org alpine:latest ls",
            returncode=0,
        )

        self.Popen.set_command(
            f"srun --nodes 2 --ntasks 2 --ntasks-per-node 1 --nodelist worker1,worker2 podman start --attach popper_1_{config.wid}",
            returncode=12,
        )

        with WorkflowRunner(config) as r:
            wf_data = {"steps": [{"uses": "docker://alpine", "args": ["ls"]}]}
            self.assertRaises(SystemExit, r.run, WorkflowParser.parse(wf_data=wf_data))

    @replace("popper.runner_slurm.os.kill", mock_kill)
    def test_exec_mpi_failure(self, mock_kill):
        config_dict = {
            "engine": {"name": "singularity", "options": {},},
            "resource_manager": {
                "name": "slurm",
                "options": {"1": {"nodes": 2, "nodelist": "worker1,worker2"}},
            },
        }

        config = ConfigLoader.load(workspace_dir="/w", config_file=config_dict)

        self.Popen.set_command(
            "sbatch "
            f"--job-name popper_1_{config.wid} "
            "--wait "
            f"--output popper_1_{config.wid}.out "
            f"popper_1_{config.wid}.sh",
            returncode=12,
        )

        self.Popen.set_command(f"tail -f popper_1_{config.wid}.out", returncode=0)

        with WorkflowRunner(config) as r:
            wf_data = {"steps": [{"uses": "docker://alpine", "args": ["ls"]}]}
            self.assertRaises(SystemExit, r.run, WorkflowParser.parse(wf_data=wf_data))


class TestSlurmDockerRunner(unittest.TestCase):
    def setUp(self):
        log.setLevel("CRITICAL")
        self.Popen = MockPopen()
        replacer = Replacer()
        replacer.replace("popper.runner_host.Popen", self.Popen)
        self.addCleanup(replacer.restore)

    def tearDown(self):
        log.setLevel("NOTSET")

    def test_create_cmd(self):
        self.maxDiff = None
        config = {"workspace_dir": "/w"}
        with DockerRunner(config=ConfigLoader.load(**config)) as drunner:
            step = Box({"args": ["-two", "-flags"]}, default_box=True)
            cmd = drunner._create_cmd(step, "foo:1.9", "container_name")

            expected = (
                "docker create"
                " --name container_name"
                " --workdir /workspace"
                " -v /w:/workspace:Z"
                " -v /var/run/docker.sock:/var/run/docker.sock"
                " foo:1.9 -two -flags"
            )

            self.assertEqual(expected.split(" "), cmd)

        config_dict = {
            "engine": {
                "name": "docker",
                "options": {
                    "privileged": True,
                    "hostname": "popper.local",
                    "domainname": "www.example.org",
                    "volumes": ["/path/in/host:/path/in/container"],
                    "environment": {"FOO": "bar"},
                },
            },
            "resource_manager": {"name": "slurm"},
        }

        config = {"workspace_dir": "/w", "config_file": config_dict}
        with DockerRunner(config=ConfigLoader.load(**config)) as drunner:
            step = Box({"args": ["-two", "-flags"]}, default_box=True)
            cmd = drunner._create_cmd(step, "foo:1.9", "container_name")

            expected = (
                "docker create --name container_name "
                "--workdir /workspace "
                "-v /w:/workspace:Z "
                "-v /var/run/docker.sock:/var/run/docker.sock "
                "-v /path/in/host:/path/in/container "
                "-e FOO=bar --privileged --hostname popper.local "
                "--domainname www.example.org"
                " foo:1.9 -two -flags"
            )

            self.assertEqual(expected.split(" "), cmd)

    @replace("popper.runner_slurm.os.kill", mock_kill)
    def test_run(self, mock_kill):
        config_dict = {
            "engine": {
                "name": "docker",
                "options": {
                    "privileged": True,
                    "hostname": "popper.local",
                    "domainname": "www.example.org",
                    "volumes": ["/path/in/host:/path/in/container"],
                    "environment": {"FOO": "bar"},
                },
            },
            "resource_manager": {
                "name": "slurm",
                "options": {"1": {"nodes": 2, "nodelist": "worker1,worker2"}},
            },
        }

        config = ConfigLoader.load(workspace_dir="/w", config_file=config_dict)

        self.Popen.set_command(
            f"srun --nodes 2 --ntasks 2 --ntasks-per-node 1 --nodelist worker1,worker2 docker rm -f popper_1_{config.wid}",
            returncode=0,
        )

        self.Popen.set_command(
            f"srun --nodes 2 --ntasks 2 --ntasks-per-node 1 --nodelist worker1,worker2 docker pull alpine:latest",
            returncode=0,
        )

        self.Popen.set_command(
            f"srun --nodes 2 --ntasks 2 --ntasks-per-node 1 --nodelist worker1,worker2 docker create --name popper_1_{config.wid} --workdir /workspace -v /w:/workspace:Z -v /path/in/host:/path/in/container -e FOO=bar --privileged --hostname popper.local --domainname www.example.org alpine:latest ls",
            returncode=0,
        )

        self.Popen.set_command(
            f"srun --nodes 2 --ntasks 2 --ntasks-per-node 1 --nodelist worker1,worker2 docker start --attach popper_1_{config.wid}",
            returncode=0,
        )

        with WorkflowRunner(config) as r:
            wf_data = {"steps": [{"uses": "docker://alpine", "args": ["ls"]}]}
            r.run(WorkflowParser.parse(wf_data=wf_data))


class TestSlurmPodmanRunner(unittest.TestCase):
    def setUp(self):
        log.setLevel("CRITICAL")
        self.Popen = MockPopen()
        replacer = Replacer()
        replacer.replace("popper.runner_host.Popen", self.Popen)
        self.addCleanup(replacer.restore)

    def tearDown(self):
        log.setLevel("NOTSET")

    def test_create_cmd(self):
        self.maxDiff = None
        config = {"workspace_dir": "/w"}
        with PodmanRunner(config=ConfigLoader.load(**config)) as prunner:
            step = Box({"args": ["-two", "-flags"]}, default_box=True)
            cmd = prunner._create_cmd(step, "foo:1.9", "container_name")

            expected = (
                "podman create"
                " --name container_name"
                " --workdir /workspace"
                " -v /w:/workspace:Z"
                " foo:1.9 -two -flags"
            )

            self.assertEqual(expected.split(" "), cmd)

        config_dict = {
            "engine": {
                "name": "podman",
                "options": {
                    "privileged": True,
                    "hostname": "popper.local",
                    "domainname": "www.example.org",
                    "volumes": ["/path/in/host:/path/in/container"],
                    "environment": {"FOO": "bar"},
                },
            },
            "resource_manager": {"name": "slurm"},
        }

        config = {"workspace_dir": "/w", "config_file": config_dict}
        with PodmanRunner(config=ConfigLoader.load(**config)) as prunner:
            step = Box({"args": ["-two", "-flags"]}, default_box=True)
            cmd = prunner._create_cmd(step, "foo:1.9", "container_name")

            expected = (
                "podman create --name container_name "
                "--workdir /workspace "
                "-v /w:/workspace:Z "
                "-v /path/in/host:/path/in/container "
                "-e FOO=bar --privileged --hostname popper.local "
                "--domainname www.example.org"
                " foo:1.9 -two -flags"
            )

            self.assertEqual(expected.split(" "), cmd)

    @replace("popper.runner_slurm.os.kill", mock_kill)
    def test_run(self, mock_kill):
        config_dict = {
            "engine": {
                "name": "podman",
                "options": {
                    "privileged": True,
                    "hostname": "popper.local",
                    "domainname": "www.example.org",
                    "volumes": ["/path/in/host:/path/in/container"],
                    "environment": {"FOO": "bar"},
                },
            },
            "resource_manager": {
                "name": "slurm",
                "options": {"1": {"nodes": 2, "nodelist": "worker1,worker2"}},
            },
        }

        config = ConfigLoader.load(workspace_dir="/w", config_file=config_dict)

        self.Popen.set_command(
            f"srun --nodes 2 --ntasks 2 --ntasks-per-node 1 --nodelist worker1,worker2 podman rm -f popper_1_{config.wid}",
            returncode=0,
        )

        self.Popen.set_command(
            f"srun --nodes 2 --ntasks 2 --ntasks-per-node 1 --nodelist worker1,worker2 podman pull alpine:latest",
            returncode=0,
        )

        self.Popen.set_command(
            f"srun --nodes 2 --ntasks 2 --ntasks-per-node 1 --nodelist worker1,worker2 podman create --name popper_1_{config.wid} --workdir /workspace -v /w:/workspace:Z -v /path/in/host:/path/in/container -e FOO=bar --privileged --hostname popper.local --domainname www.example.org alpine:latest ls",
            returncode=0,
        )

        self.Popen.set_command(
            f"srun --nodes 2 --ntasks 2 --ntasks-per-node 1 --nodelist worker1,worker2 podman start --attach popper_1_{config.wid}",
            returncode=0,
        )

        with WorkflowRunner(config) as r:
            wf_data = {"steps": [{"uses": "docker://alpine", "args": ["ls"]}]}
            r.run(WorkflowParser.parse(wf_data=wf_data))


class TestSlurmSingularityRunner(unittest.TestCase):
    def setUp(self):
        self.Popen = MockPopen()
        replacer = Replacer()
        replacer.replace("popper.runner_host.Popen", self.Popen)
        self.addCleanup(replacer.restore)

    def tearDown(self):
        log.setLevel("NOTSET")

    def test_create_cmd(self):
        config = ConfigLoader.load(workspace_dir="/w")
        with SingularityRunner(config=config) as sr:
            step = Box({"args": ["-two", "-flags"]}, default_box=True)
            sr._container = "c1.sif"
            cmd = sr._create_cmd(step, "c1.sif")

            expected = (
                "singularity run"
                " --userns --pwd /workspace"
                " --bind /w:/workspace"
                " c1.sif"
                " -two -flags"
            )

            self.assertEqual(expected.split(" "), cmd)

        config_dict = {
            "engine": {
                "name": "singularity",
                "options": {
                    "hostname": "popper.local",
                    "ipc": True,
                    "bind": ["/path/in/host:/path/in/container"],
                },
            },
            "resource_manager": {"name": "slurm"},
        }

        config = ConfigLoader.load(workspace_dir="/w", config_file=config_dict)

        with SingularityRunner(config=config) as sr:
            step = Box({"args": ["-two", "-flags"]}, default_box=True)
            sr._container = "c2.sif"
            cmd = sr._create_cmd(step, "c2.sif")

            # fmt: off
            expected = f"singularity run --userns --pwd /workspace --bind /w:/workspace --bind /path/in/host:/path/in/container --hostname popper.local --ipc c2.sif -two -flags"
            # fmt: on
            self.assertEqual(expected.split(" "), cmd)

    @replace("popper.runner_slurm.os.kill", mock_kill)
    def test_run(self, mock_kill):
        config_dict = {
            "engine": {
                "name": "singularity",
                "options": {
                    "hostname": "popper.local",
                    "bind": ["/path/in/host:/path/in/container"],
                },
            },
            "resource_manager": {
                "name": "slurm",
                "options": {"1": {"nodes": 2, "nodelist": "worker1,worker2"}},
            },
        }

        config = ConfigLoader.load(workspace_dir="/w", config_file=config_dict)

        # fmt: off
        self.Popen.set_command(
            f"sbatch --job-name popper_1_{config.wid} --wait --output popper_1_{config.wid}.out popper_1_{config.wid}.sh",
            returncode=0,
        )
        # fmt: on

        self.Popen.set_command(f"tail -f popper_1_{config.wid}.out", returncode=0)

        with WorkflowRunner(config) as r:
            wf_data = {"steps": [{"uses": "docker://alpine", "args": ["ls"]}]}
            r.run(WorkflowParser.parse(wf_data=wf_data))

        with open(f"popper_1_{config.wid}.sh", "r") as f:
            # fmt: off
            expected = f"""#!/bin/bash
#SBATCH --nodes=2
#SBATCH --ntasks=2
#SBATCH --ntasks-per-node=1
#SBATCH --nodelist=worker1,worker2

mpirun singularity run --userns --pwd /workspace --bind /w:/workspace --bind /path/in/host:/path/in/container --hostname popper.local popper_1_{config.wid}.sif ls"""
            # fmt: on
            actual = f.read()
            self.assertEqual(expected, actual)

        config_dict = {
            "engine": {
                "name": "singularity",
                "options": {
                    "hostname": "popper.local",
                    "bind": ["/path/in/host:/path/in/container"],
                },
            },
            "resource_manager": {
                "name": "slurm",
                "options": {
                    "1": {"mpi": False, "nodes": 2, "nodelist": "worker1,worker2"}
                },
            },
        }

        config = ConfigLoader.load(workspace_dir="/w", config_file=config_dict)

        self.Popen.set_command(
            f"srun --nodes 2 --ntasks 2 --ntasks-per-node 1 --nodelist worker1,worker2 rm -rf popper_1_{config.wid}.sif",
            returncode=0,
        )

        self.Popen.set_command(
            f"srun --nodes 2 --ntasks 2 --ntasks-per-node 1 --nodelist worker1,worker2 singularity pull docker://alpine:latest",
            returncode=0,
        )

        self.Popen.set_command(
            f"srun --nodes 2 --ntasks 2 --ntasks-per-node 1 --nodelist worker1,worker2 singularity run --userns --pwd /workspace --bind /w:/workspace --bind /path/in/host:/path/in/container --hostname popper.local popper_1_{config.wid}.sif ls",
            returncode=0,
        )

        with WorkflowRunner(config) as r:
            wf_data = {"steps": [{"uses": "docker://alpine", "args": ["ls"]}]}
            r.run(WorkflowParser.parse(wf_data=wf_data))
