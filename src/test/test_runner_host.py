import os
import shutil
import time
import unittest

from testfixtures import LogCapture
from subprocess import Popen

import popper.utils as pu

from popper.config import ConfigLoader
from popper.parser import WorkflowParser
from popper.runner import WorkflowRunner
from popper.runner_host import HostRunner, DockerRunner, SingularityRunner
from popper.cli import log as log
from .test_common import PopperTest

import docker

from box import Box


class TestHostHostRunner(PopperTest):
    def setUp(self):
        log.setLevel("CRITICAL")

    def test_host_run(self):

        repo = self.mk_repo()
        conf = ConfigLoader.load(workspace_dir=repo.working_dir)

        with WorkflowRunner(conf) as r:
            wf_data = {
                "steps": [{"uses": "sh", "runs": ["cat"], "args": ["README.md"],}]
            }
            r.run(WorkflowParser.parse(wf_data=wf_data))

            wf_data = {
                "steps": [
                    {
                        "uses": "sh",
                        "runs": ["bash", "-c", "echo $FOO > hello.txt ; pwd"],
                        "env": {"FOO": "bar"},
                    }
                ]
            }
            r.run(WorkflowParser.parse(wf_data=wf_data))
            with open(os.path.join(repo.working_dir, "hello.txt"), "r") as f:
                self.assertEqual(f.read(), "bar\n")

            wf_data = {"steps": [{"uses": "sh", "runs": ["nocommandisnamedlikethis"]}]}
            self.assertRaises(SystemExit, r.run, WorkflowParser.parse(wf_data=wf_data))

            # check exit code 78
            wf_data = {
                "steps": [
                    {"uses": "sh", "runs": ["touch", "one.txt"]},
                    {"uses": "sh", "runs": ["bash", "-c", "exit 78"]},
                    {"uses": "sh", "runs": ["touch", "two.txt"]},
                ]
            }
            r.run(WorkflowParser.parse(wf_data=wf_data))
            self.assertTrue(os.path.isfile(os.path.join(repo.working_dir, "one.txt")))
            self.assertFalse(os.path.isfile(os.path.join(repo.working_dir, "two.txt")))

        repo.close()
        shutil.rmtree(repo.working_dir, ignore_errors=True)

    def test_exec_cmd(self):
        cmd = ["echo", "hello-world"]
        pid, ecode, output = HostRunner._exec_cmd(cmd, logging=False)
        self.assertGreater(pid, 0)
        self.assertEqual(ecode, 0)
        self.assertEqual(output, "hello-world\n")

        with LogCapture("popper") as logc:
            pid, ecode, output = HostRunner._exec_cmd(cmd)
            self.assertGreater(pid, 0)
            self.assertEqual(ecode, 0)
            self.assertEqual(output, "")
            logc.check_present(("popper", "STEP_INFO", "hello-world\n"))

        cmd = ["env"]
        pid, ecode, output = HostRunner._exec_cmd(
            cmd, env={"TESTACION": "test"}, cwd="/tmp", logging=False
        )
        self.assertGreater(pid, 0)
        self.assertEqual(ecode, 0)
        self.assertTrue("TESTACION" in output)

        _pids = set()
        _, _, _ = HostRunner._exec_cmd(["sleep", "2"], pids=_pids)
        self.assertEqual(len(_pids), 1)

    def test_stop_running_tasks(self):
        with HostRunner() as hr:
            with Popen(["sleep", "2000"]) as p:
                pid = p.pid
                hr._spawned_pids.add(pid)
                hr.stop_running_tasks()
        time.sleep(2)
        self.assertRaises(ProcessLookupError, os.kill, pid, 0)


class TestHostDockerRunner(PopperTest):
    def setUp(self):
        log.setLevel("CRITICAL")

    @unittest.skipIf(os.environ.get("ENGINE", "docker") != "docker", "ENGINE != docker")
    def test_create_container(self):
        config = ConfigLoader.load()
        step = Box(
            {
                "uses": "docker://alpine:3.9",
                "runs": ["echo hello"],
                "id": "kontainer_one",
            },
            default_box=True,
        )
        cid = pu.sanitized_name(step.id, config.wid)
        with DockerRunner(init_docker_client=True, config=config) as dr:
            c = dr._create_container(cid, step)
            self.assertEqual(c.status, "created")
            c.remove()
        step = Box(
            {
                "uses": "docker://alpine:3.9",
                "runs": ["echo", "hello_world"],
                "id": "KoNtAiNeR tWo",
            },
            default_box=True,
        )
        cid = pu.sanitized_name(step.id, config.wid)
        with DockerRunner(init_docker_client=True, config=config) as dr:
            c = dr._create_container(cid, step)
            self.assertEqual(c.status, "created")
            c.remove()

    @unittest.skipIf(os.environ.get("ENGINE", "docker") != "docker", "ENGINE != docker")
    def test_stop_running_tasks(self):
        with DockerRunner() as dr:
            dclient = docker.from_env()
            c1 = dclient.containers.run(
                "debian:buster-slim", "sleep 20000", detach=True
            )
            c2 = dclient.containers.run("alpine:3.9", "sleep 10000", detach=True)
            dr._spawned_containers.add(c1)
            dr._spawned_containers.add(c2)
            dr.stop_running_tasks()
            self.assertEqual(c1.status, "created")
            self.assertEqual(c2.status, "created")
            dclient.close()

    @unittest.skipIf(os.environ.get("ENGINE", "docker") != "docker", "ENGINE != docker")
    def test_get_container_kwargs(self):
        step = Box(
            {
                "uses": "popperized/bin/sh@master",
                "args": ["ls"],
                "id": "one",
                "dir": "/tmp/",
            },
            default_box=True,
        )

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
        }

        config = ConfigLoader.load(
            config_file=config_dict, workspace_dir="/path/to/workdir"
        )

        with DockerRunner(init_docker_client=False, config=config) as dr:
            args = dr._get_container_kwargs(step, "alpine:3.9", "container_a")

            self.assertEqual(
                args,
                {
                    "image": "alpine:3.9",
                    "command": ["ls"],
                    "name": "container_a",
                    "volumes": [
                        "/path/to/workdir:/workspace",
                        "/var/run/docker.sock:/var/run/docker.sock",
                        "/path/in/host:/path/in/container",
                    ],
                    "working_dir": "/tmp/",
                    "environment": {"FOO": "bar"},
                    "entrypoint": None,
                    "detach": True,
                    "stdin_open": False,
                    "tty": False,
                    "privileged": True,
                    "hostname": "popper.local",
                    "domainname": "www.example.org",
                },
            )

        # check container kwargs when pty is enabled
        config = ConfigLoader.load(
            config_file=config_dict, workspace_dir="/path/to/workdir", pty=True
        )

        with DockerRunner(init_docker_client=False, config=config) as dr:
            args = dr._get_container_kwargs(step, "alpine:3.9", "container_a")

            self.assertEqual(
                args,
                {
                    "image": "alpine:3.9",
                    "command": ["ls"],
                    "name": "container_a",
                    "volumes": [
                        "/path/to/workdir:/workspace",
                        "/var/run/docker.sock:/var/run/docker.sock",
                        "/path/in/host:/path/in/container",
                    ],
                    "working_dir": "/tmp/",
                    "environment": {"FOO": "bar"},
                    "entrypoint": None,
                    "detach": False,
                    "stdin_open": True,
                    "tty": True,
                    "privileged": True,
                    "hostname": "popper.local",
                    "domainname": "www.example.org",
                },
            )

    @unittest.skipIf(os.environ.get("ENGINE", "docker") != "docker", "ENGINE != docker")
    def test_get_build_info(self):
        step = Box(
            {"uses": "popperized/bin/sh@master", "args": ["ls"], "id": "one",},
            default_box=True,
        )
        with DockerRunner(init_docker_client=False) as dr:
            build, img, tag, build_sources = dr._get_build_info(step)
            self.assertEqual(build, True)
            self.assertEqual(img, "popperized/bin")
            self.assertEqual(tag, "master")
            self.assertTrue(f"{os.environ['HOME']}/.cache/popper" in build_sources)
            self.assertTrue("github.com/popperized/bin/sh" in build_sources)

            step = Box(
                {
                    "uses": "docker://alpine:3.9",
                    "runs": ["sh", "-c", "echo $FOO > hello.txt ; pwd"],
                    "env": {"FOO": "bar"},
                    "id": "1",
                },
                default_box=True,
            )

        with DockerRunner(init_docker_client=False) as dr:
            build, img, tag, build_sources = dr._get_build_info(step)
            self.assertEqual(build, False)
            self.assertEqual(img, "alpine")
            self.assertEqual(tag, "3.9")
            self.assertEqual(build_sources, None)

    @unittest.skipIf(os.environ.get("ENGINE", "docker") != "docker", "ENGINE != docker")
    def test_docker_basic_run(self):
        repo = self.mk_repo()
        conf = ConfigLoader.load(workspace_dir=repo.working_dir)

        with WorkflowRunner(conf) as r:
            wf_data = {"steps": [{"uses": "popperized/bin/sh@master", "args": ["ls"],}]}
            r.run(WorkflowParser.parse(wf_data=wf_data))

            wf_data = {
                "steps": [
                    {
                        "uses": "docker://alpine:3.9",
                        "args": ["sh", "-c", "echo $FOO > hello.txt ; pwd"],
                        "env": {"FOO": "bar"},
                    }
                ]
            }
            r.run(WorkflowParser.parse(wf_data=wf_data))
            with open(os.path.join(repo.working_dir, "hello.txt"), "r") as f:
                self.assertEqual(f.read(), "bar\n")

            wf_data = {
                "steps": [
                    {
                        "uses": "docker://alpine:3.9",
                        "args": ["nocommandisnamedlikethis"],
                    }
                ]
            }
            self.assertRaises(SystemExit, r.run, WorkflowParser.parse(wf_data=wf_data))

        repo.close()
        shutil.rmtree(repo.working_dir, ignore_errors=True)


class TestHostSingularityRunner(PopperTest):
    def setUp(self):
        log.setLevel("CRITICAL")

    @unittest.skipIf(
        os.environ.get("ENGINE", "docker") != "singularity", "ENGINE != singularity"
    )
    def test_get_recipe_file(self):
        repo = self.mk_repo()
        build_ctx_path = repo.working_dir

        with open(os.path.join(build_ctx_path, "Dockerfile"), "w") as f:
            f.write(
                """
FROM alpine
RUN apk update && apk add bash
ADD README.md /
ENTRYPOINT ["/bin/bash"]"""
            )

        singularity_file = SingularityRunner._get_recipe_file(
            build_ctx_path, "sample.sif"
        )
        self.assertEqual(
            singularity_file, os.path.join(build_ctx_path, "Singularity.sample")
        )
        self.assertEqual(os.path.exists(singularity_file), True)
        with open(singularity_file) as f:
            self.assertEqual(
                f.read(),
                '''Bootstrap: docker
From: alpine
%files
README.md /
%post

apk update && apk add bash
%runscript
exec /bin/bash "$@"
%startscript
exec /bin/bash "$@"''',
            )

        os.remove(os.path.join(build_ctx_path, "Dockerfile"))
        self.assertRaises(
            SystemExit, SingularityRunner._get_recipe_file, build_ctx_path, "sample.sif"
        )

    @unittest.skipIf(
        os.environ.get("ENGINE", "docker") != "singularity", "ENGINE != singularity"
    )
    def test_create_container(self):
        config = ConfigLoader.load()
        step_one = Box(
            {
                "uses": "docker://alpine:3.9",
                "runs": ["echo hello"],
                "id": "kontainer_one",
            },
            default_box=True,
        )

        step_two = Box(
            {
                "uses": "popperized/bin/sh@master",
                "args": ["ls"],
                "id": "kontainer_two",
            },
            default_box=True,
        )

        cid_one = pu.sanitized_name(step_one.id, config.wid)
        cid_two = pu.sanitized_name(step_two.id, config.wid)

        with SingularityRunner(config=config) as sr:
            sr._setup_singularity_cache()
            sr._create_container(step_one, cid_one)
            self.assertEqual(
                os.path.exists(os.path.join(sr._singularity_cache, cid_one)), True
            )
            os.remove(os.path.join(sr._singularity_cache, cid_one))

        with SingularityRunner(config=config) as sr:
            sr._setup_singularity_cache()
            sr._create_container(step_one, cid_two)
            self.assertEqual(
                os.path.exists(os.path.join(sr._singularity_cache, cid_two)), True
            )
            os.remove(os.path.join(sr._singularity_cache, cid_two))

    @unittest.skipIf(
        os.environ.get("ENGINE", "docker") != "singularity", "ENGINE != singularity"
    )
    def test_setup_singularity_cache(self):
        config = ConfigLoader.load()
        with SingularityRunner(config=config) as sr:
            sr._setup_singularity_cache()
            self.assertEqual(
                f'{os.environ["HOME"]}/.cache/popper/singularity/{config.wid}',
                sr._singularity_cache,
            )

    @unittest.skipIf(
        os.environ.get("ENGINE", "docker") != "singularity", "ENGINE != singularity"
    )
    def test_get_container_options(self):
        config_dict = {
            "engine": {
                "name": "singularity",
                "options": {
                    "hostname": "popper.local",
                    "ipc": True,
                    "bind": ["/path/in/host:/path/in/container"],
                },
            }
        }

        config = ConfigLoader.load(config_file=config_dict)
        with SingularityRunner(config=config) as sr:
            sr._setup_singularity_cache()
            options = sr._get_container_options()
            self.assertEqual(
                options,
                [
                    "--userns",
                    "--pwd",
                    "/workspace",
                    "--bind",
                    f"{os.getcwd()}:/workspace",
                    "--bind",
                    "/path/in/host:/path/in/container",
                    "--hostname",
                    "popper.local",
                    "--ipc",
                ],
            )

    @unittest.skipIf(
        os.environ.get("ENGINE", "docker") != "singularity", "ENGINE != singularity"
    )
    def test_get_build_info(self):
        step = Box(
            {"uses": "popperized/bin/sh@master", "args": ["ls"], "name": "one",},
            default_box=True,
        )
        with SingularityRunner() as sr:
            build, img, build_sources = sr._get_build_info(step)
            self.assertEqual(build, True)
            self.assertEqual(img, "popperized/bin")
            self.assertTrue(f"{os.environ['HOME']}/.cache/popper" in build_sources)
            self.assertTrue(f"github.com/popperized/bin/sh" in build_sources)

            step = Box(
                {
                    "uses": "docker://alpine:3.9",
                    "runs": ["sh", "-c", "echo $FOO > hello.txt ; pwd"],
                    "env": {"FOO": "bar"},
                    "name": "1",
                },
                default_box=True,
            )

        with SingularityRunner() as sr:
            build, img, build_sources = sr._get_build_info(step)
            self.assertEqual(build, False)
            self.assertEqual(img, "docker://alpine:3.9")
            self.assertEqual(build_sources, None)

    @unittest.skipIf(
        os.environ.get("ENGINE", "docker") != "singularity", "ENGINE != singularity"
    )
    def test_singularity_start(self):
        repo = self.mk_repo()
        conf = ConfigLoader.load(
            engine_name="singularity", workspace_dir=repo.working_dir
        )

        step = Box(
            {
                "uses": "docker://alpine:3.9",
                "runs": ["echo", "hello"],
                "name": "test_1",
            },
            default_box=True,
        )
        cid = pu.sanitized_name(step["name"], conf.wid)
        with SingularityRunner(config=conf) as sr:
            sr._setup_singularity_cache()
            sr._container = os.path.join(sr._singularity_cache, cid)
            sr._create_container(step, cid)
            self.assertEqual(sr._singularity_start(step, cid), 0)

        # step = Box({
        #     'uses': 'library://library/default/alpine:3.7',
        #     'runs': ['echo', 'hello'],
        #     'name': 'test_2'
        # }, default_box=True)
        # cid = pu.sanitized_name(step['name'], conf.wid)
        # with SingularityRunner(config=conf) as sr:
        #     sr._setup_singularity_cache()
        #     sr._container = os.path.join(sr._singularity_cache, cid)
        #     sr._create_container(step, cid)
        #     self.assertEqual(sr._singularity_start(step, cid), 0)

        # step = Box({
        #     'uses': 'shub://divetea/debian:latest',
        #     'runs': ['echo', 'hello'],
        #     'name': 'test_3'
        # }, default_box=True)
        # cid = pu.sanitized_name(step['name'], conf.wid)
        # with SingularityRunner(config=conf) as sr:
        #     sr._setup_singularity_cache()
        #     sr._container = os.path.join(sr._singularity_cache, cid)
        #     sr._create_container(step, cid)
        #     self.assertEqual(sr._singularity_start(step, cid), 0)

        step = Box(
            {
                "uses": "docker://alpine:3.9",
                "runs": ["ecdhoo", "hello"],
                "name": "test_4",
            },
            default_box=True,
        )
        cid = pu.sanitized_name(step["name"], conf.wid)
        with SingularityRunner(config=conf) as sr:
            sr._setup_singularity_cache()
            sr._container = os.path.join(sr._singularity_cache, cid)
            sr._create_container(step, cid)
            self.assertNotEqual(sr._singularity_start(step, cid), 0)

        with WorkflowRunner(conf) as r:
            wf_data = {"steps": [{"uses": "popperized/bin/sh@master", "args": ["ls"],}]}
            r.run(WorkflowParser.parse(wf_data=wf_data))

            wf_data = {
                "steps": [
                    {
                        "uses": "docker://alpine:3.9",
                        "args": ["sh", "-c", "echo $FOO > hello.txt ; pwd"],
                        "env": {"FOO": "bar"},
                    }
                ]
            }
            r.run(WorkflowParser.parse(wf_data=wf_data))
            with open(os.path.join(repo.working_dir, "hello.txt"), "r") as f:
                self.assertEqual(f.read(), "bar\n")

            wf_data = {
                "steps": [
                    {
                        "uses": "docker://alpine:3.9",
                        "args": ["nocommandisnamedlikethis"],
                    }
                ]
            }
            self.assertRaises(SystemExit, r.run, WorkflowParser.parse(wf_data=wf_data))

        repo.close()
