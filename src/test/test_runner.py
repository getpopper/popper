import os
import unittest
import shutil

from unittest.mock import patch

import popper.scm as scm
from popper.cli import log
from popper.config import ConfigLoader
from popper.parser import WorkflowParser
from popper.runner import WorkflowRunner, StepRunner

from .test_common import PopperTest

from box import Box


class TestWorkflowRunner(unittest.TestCase):
    def setUp(self):
        log.setLevel("CRITICAL")

    def test_check_secrets(self):
        wf_data = {
            "steps": [
                {
                    "uses": "docker://alpine:3.9",
                    "args": ["ls", "-ltr"],
                    "secrets": ["SECRET_ONE", "SECRET_TWO"],
                }
            ]
        }
        wf = WorkflowParser.parse(wf_data=wf_data)

        # in dry-run, secrets are ignored
        runner = WorkflowRunner(ConfigLoader.load(dry_run=True))
        runner._process_secrets(wf)

        # now go back to not dry-running
        runner = WorkflowRunner(ConfigLoader.load())

        # when CI=true it should fail
        os.environ["CI"] = "true"
        self.assertRaises(SystemExit, runner._process_secrets, wf)

        # but it should be fine if we allow undefined secrets
        runner = WorkflowRunner(ConfigLoader.load(allow_undefined_secrets_in_ci=True))
        runner._process_secrets(wf)

        # add one secret
        os.environ["SECRET_ONE"] = "1234"

        # it should fail, as we're missing one
        runner = WorkflowRunner(ConfigLoader.load())
        self.assertRaises(SystemExit, runner._process_secrets, wf)

        os.environ.pop("CI")

        # now is fine
        with patch("getpass.getpass", return_value="5678"):
            runner._process_secrets(wf)

        # pop the other
        os.environ.pop("SECRET_ONE")

    def test_clone_repos(self):
        wf_data = {"steps": [{"uses": "popperized/bin/sh@master"}]}
        wf = WorkflowParser.parse(wf_data=wf_data)

        cache_dir = os.path.join(os.environ["HOME"], ".cache/popper/")

        # clone repos in the default cache directory.
        conf = ConfigLoader.load()
        runner = WorkflowRunner(conf)
        runner._clone_repos(wf)
        step_dir = os.path.join(cache_dir, conf.wid, "github.com/popperized/bin")
        self.assertTrue(os.path.exists(step_dir))

        # clone repos in custom cache directory
        os.environ["POPPER_CACHE_DIR"] = "/tmp/smdir"
        conf = ConfigLoader.load()
        runner = WorkflowRunner(conf)
        runner._clone_repos(wf)
        step_dir = os.path.join("/tmp/smdir", conf.wid, "github.com/popperized/bin")
        self.assertTrue(os.path.exists(step_dir))
        os.environ.pop("POPPER_CACHE_DIR")

        # check failure when container is not available and we skip cloning
        shutil.rmtree("/tmp/smdir")
        shutil.rmtree(cache_dir)
        conf = ConfigLoader.load(skip_clone=True)
        runner = WorkflowRunner(conf)
        self.assertRaises(SystemExit, runner._clone_repos, wf)

    def test_steprunner_factory(self):
        with WorkflowRunner(ConfigLoader.load()) as r:
            self.assertEqual(
                "HostRunner", r._step_runner("host", None).__class__.__name__
            )


class TestStepRunner(PopperTest):
    def setUp(self):
        log.setLevel("CRITICAL")

    def test_prepare_environment_without_git(self):
        step = Box(
            {"name": "a", "env": {"FOO": "BAR"}, "secrets": ["A"]}, default_box=True
        )
        os.environ["A"] = "BC"

        with StepRunner(ConfigLoader.load(workspace_dir="/tmp/foo")) as r:
            env = r._prepare_environment(step, {"other": "b"})
            self.assertDictEqual({"FOO": "BAR", "A": "BC", "other": "b"}, env)
            os.environ.pop("A")

            # secret undefined should return an empty variable
            env = r._prepare_environment(step, {"other": "b"})
            self.assertDictEqual({"FOO": "BAR", "A": "", "other": "b"}, env)

    def test_prepare_environment_with_git(self):
        repo = self.mk_repo(tag="a-tag")
        conf = ConfigLoader.load(workspace_dir=repo.working_dir)
        with StepRunner(conf) as r:
            step = Box(
                {"name": "a", "env": {"FOO": "BAR"}, "secrets": ["A"]}, default_box=True
            )
            os.environ["A"] = "BC"
            env = r._prepare_environment(step, {"other": "b"})
            expected = {
                "FOO": "BAR",
                "A": "BC",
                "other": "b",
                "GIT_COMMIT": conf.git_commit,
                "GIT_BRANCH": conf.git_branch,
                "GIT_SHA_SHORT": conf.git_sha_short,
                "GIT_REMOTE_ORIGIN_URL": conf.git_remote_origin_url,
                "GIT_TAG": conf.git_tag,
            }
            self.assertDictEqual(expected, env)
            os.environ.pop("A")

    def test_get_build_info(self):
        step = Box(
            {"uses": "popperized/bin/sh@master", "args": ["ls"], "id": "one",},
            default_box=True,
        )
        with StepRunner() as r:
            build, _, img, tag, build_ctx_path = r._get_build_info(step)
            self.assertEqual(build, True)
            self.assertEqual(img, "popperized/bin")
            self.assertEqual(tag, "master")
            self.assertTrue(f"{os.environ['HOME']}/.cache/popper" in build_ctx_path)
            self.assertTrue("github.com/popperized/bin/sh" in build_ctx_path)

        step = Box(
            {
                "uses": "docker://alpine:3.9",
                "runs": ["sh", "-c", "echo $FOO > hello.txt ; pwd"],
                "env": {"FOO": "bar"},
                "id": "1",
            },
            default_box=True,
        )
        with StepRunner() as r:
            build, _, img, tag, build_sources = r._get_build_info(step)
            self.assertEqual(build, False)
            self.assertEqual(img, "alpine")
            self.assertEqual(tag, "3.9")
            self.assertEqual(build_sources, None)

        step = Box({"uses": "./", "args": ["ls"], "id": "one",}, default_box=True,)
        conf = ConfigLoader.load(workspace_dir="/tmp")
        with StepRunner(config=conf) as r:
            build, _, img, tag, build_ctx_path = r._get_build_info(step)
            self.assertEqual(build, True)
            self.assertEqual(img, "popper_one_step")
            self.assertEqual(tag, "na")
            self.assertEqual(build_ctx_path, f"{os.path.realpath('/tmp')}/./")

        # test within a git repo
        repo = self.mk_repo()
        conf = ConfigLoader.load(workspace_dir=repo.working_dir)
        with StepRunner(config=conf) as r:
            build, _, img, tag, build_ctx_path = r._get_build_info(step)
            self.assertEqual(build, True)
            self.assertEqual(img, "popper_one_step")
            self.assertEqual(tag, scm.get_sha(repo, short=7))
            self.assertEqual(build_ctx_path, f"{os.path.realpath(repo.working_dir)}/./")

        step = Box(
            {
                "uses": "docker://alpine:3.9",
                "runs": ["sh", "-c", "echo $FOO > hello.txt ; pwd"],
                "env": {"FOO": "bar"},
                "name": "1",
            },
            default_box=True,
        )
        with StepRunner() as r:
            build, img_full, _, _, build_ctx_path = r._get_build_info(step)
            self.assertEqual(build, False)
            self.assertEqual(img_full, "docker://alpine:3.9")
            self.assertEqual(build_ctx_path, None)

    def test_get_container_kwargs(self):
        step = Box(
            {
                "uses": "popperized/bin/sh@master",
                "args": ["ls"],
                "id": "one",
                "dir": "/tmp/",
                "options": {"ports": {"8888/tcp": 8888}},
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

        with StepRunner(config=config) as r:
            args = r._get_container_kwargs(step, "alpine:3.9", "container_a")
            self.assertEqual(
                args,
                {
                    "image": "alpine:3.9",
                    "command": ["ls"],
                    "name": "container_a",
                    "volumes": [
                        "/path/to/workdir:/workspace:Z",
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
                    "ports": {"8888/tcp": 8888},
                },
            )

        # check container kwargs when pty is enabled
        config = ConfigLoader.load(
            config_file=config_dict, workspace_dir="/path/to/workdir", pty=True
        )

        with StepRunner(config=config) as r:
            args = r._get_container_kwargs(step, "alpine:3.9", "container_a")

            self.assertEqual(
                args,
                {
                    "image": "alpine:3.9",
                    "command": ["ls"],
                    "name": "container_a",
                    "volumes": [
                        "/path/to/workdir:/workspace:Z",
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
                    "ports": {"8888/tcp": 8888},
                },
            )
