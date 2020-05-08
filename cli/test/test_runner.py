import os
import unittest
import shutil

from unittest.mock import patch

from popper.cli import log
from popper.config import PopperConfig
from popper.parser import YMLWorkflow
from popper.runner import WorkflowRunner, StepRunner

from .test_common import PopperTest


class TestWorkflowRunner(unittest.TestCase):
    def setUp(self):
        log.setLevel("CRITICAL")

    def test_check_secrets(self):
        wf = YMLWorkflow(
            """
        version: '1'
        steps:
        - uses: docker://alpine:3.9
          args: ["ls -ltr"]
          secrets: ["SECRET_ONE", "SECRET_TWO"]
        """
        )
        wf.parse()

        # in dry-run, secrets are ignored
        runner = WorkflowRunner(PopperConfig(dry_run=True))
        runner._process_secrets(wf)

        # now go back to not dry-running
        runner = WorkflowRunner(PopperConfig())

        # when CI=true it should fail
        os.environ["CI"] = "true"
        self.assertRaises(SystemExit, runner._process_secrets, wf)

        # add one secret
        os.environ["SECRET_ONE"] = "1234"

        # it should fail again, as we're missing one
        self.assertRaises(SystemExit, runner._process_secrets, wf)

        os.environ.pop("CI")

        # now is fine
        with patch("getpass.getpass", return_value="5678"):
            runner._process_secrets(wf)

        # pop the other
        os.environ.pop("SECRET_ONE")

    def test_clone_repos(self):
        wf = YMLWorkflow(
            """
        version: '1'
        steps:
        - uses: popperized/bin/sh@master
        """
        )
        wf.parse()

        conf = PopperConfig()
        cache_dir = os.path.join(os.environ["HOME"], ".cache/popper/")

        # clone repos in the default cache directory.
        runner = WorkflowRunner(conf)
        runner._clone_repos(wf)
        step_dir = os.path.join(cache_dir, conf.wid, "github.com/popperized/bin")
        self.assertTrue(os.path.exists(step_dir))

        # clone repos in custom cache directory
        os.environ["POPPER_CACHE_DIR"] = "/tmp/smdir"
        runner._clone_repos(wf)
        step_dir = os.path.join("/tmp/smdir", conf.wid, "github.com/popperized/bin")
        self.assertTrue(os.path.exists(step_dir))
        os.environ.pop("POPPER_CACHE_DIR")

        # check failure when container is not available and we skip cloning
        shutil.rmtree("/tmp/smdir")
        shutil.rmtree(cache_dir)
        conf = PopperConfig(skip_clone=True)
        runner = WorkflowRunner(conf)
        self.assertRaises(SystemExit, runner._clone_repos, wf)

    def test_steprunner_factory(self):
        with WorkflowRunner(PopperConfig()) as r:
            self.assertEqual(
                "HostRunner", r._step_runner("host", None).__class__.__name__
            )
            self.assertEqual(
                "DockerRunner", r._step_runner("docker", None).__class__.__name__
            )

    def test_setup_base_cache(self):
        cache_dir = WorkflowRunner._setup_base_cache()
        try:
            self.assertEqual(os.environ["XDG_CACHE_HOME"], cache_dir)
        except KeyError:
            self.assertEqual(
                os.path.join(os.environ["HOME"], ".cache/popper"), cache_dir
            )

        os.environ["POPPER_CACHE_DIR"] = "/tmp/popper"
        cache_dir = WorkflowRunner._setup_base_cache()
        self.assertEqual("/tmp/popper", cache_dir)
        os.environ.pop("POPPER_CACHE_DIR")


class TestStepRunner(PopperTest):
    def setUp(self):
        log.setLevel("CRITICAL")

    def test_prepare_environment_without_git(self):
        with StepRunner(PopperConfig(workspace_dir="/tmp/foo")) as r:
            step = {"name": "a", "env": {"FOO": "BAR"}, "secrets": ["A"]}
            os.environ["A"] = "BC"
            env = r._prepare_environment(step, {"other": "b"})
            self.assertDictEqual({"FOO": "BAR", "A": "BC", "other": "b"}, env)
            os.environ.pop("A")

    def test_prepare_environment_with_git(self):
        repo = self.mk_repo()
        conf = PopperConfig(workspace_dir=repo.working_dir)
        with StepRunner(conf) as r:
            step = {"name": "a", "env": {"FOO": "BAR"}, "secrets": ["A"]}
            os.environ["A"] = "BC"
            env = r._prepare_environment(step, {"other": "b"})
            expected = {
                "FOO": "BAR",
                "A": "BC",
                "other": "b",
                "GIT_COMMIT": conf.git_commit,
                "GIT_BRANCH": conf.git_branch,
                "GIT_SHA_SHORT": conf.git_sha_short,
            }
            self.assertDictEqual(expected, env)
            os.environ.pop("A")
