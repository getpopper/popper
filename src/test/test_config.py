import os

from popper.config import ConfigLoader
from popper.cli import log

from .test_common import PopperTest

from box import Box


class TestPopperConfig(PopperTest):
    def setUp(self):
        log.setLevel("CRITICAL")
        self.maxDiff = None

    def tearDown(self):
        log.setLevel("NOTSET")

    def test_config_defaults(self):
        conf = ConfigLoader.load()
        expected = Box(
            {
                "skip_clone": False,
                "engine_name": "docker",
                "engine_opts": {},
                "resman_name": "host",
                "resman_opts": {},
                "skip_pull": False,
                "dry_run": False,
                "workspace_dir": os.getcwd(),
                "quiet": False,
                "reuse": False,
                "pty": False,
                "allow_undefined_secrets_in_ci": False,
            },
            default_box=True,
        )

        self.assertEqual(expected, TestPopperConfig.extract_dict(expected, conf))

    def test_config_non_defaults(self):
        expected = {
            "skip_clone": True,
            "skip_pull": True,
            "dry_run": True,
            "workspace_dir": os.path.realpath("/tmp/foo"),
            "quiet": True,
            "reuse": True,
            "pty": True,
            "allow_undefined_secrets_in_ci": True,
        }
        conf = ConfigLoader.load(**expected)
        self.assertEqual(expected, TestPopperConfig.extract_dict(expected, conf))

    def test_config_without_git_repo(self):
        conf = ConfigLoader.load(workspace_dir="/tmp/foo")
        self.assertTrue(not conf.git_commit)
        self.assertTrue(not conf.git_branch)
        self.assertTrue(not conf.git_sha_short)
        self.assertTrue(not conf.git_tag)

    def test_config_with_git_repo(self):
        r = self.mk_repo(tag="a-tag")
        conf = ConfigLoader.load(workspace_dir=r.working_dir)
        sha = r.head.object.hexsha
        self.assertEqual(r.git.rev_parse(sha), conf.git_commit)
        self.assertEqual(r.git.rev_parse(sha, short=7), conf.git_sha_short)
        self.assertEqual(r.active_branch.name, conf.git_branch)
        self.assertEqual(r.git.tag("--points-at", "HEAD"), conf.git_tag)

    def test_config_from_file(self):
        config = {
            "engine": {"options": {"privileged": True}},
            "resource_manager": {"options": {"foo": "bar"}},
        }
        kwargs = {"config_file": config}

        # engine name missing
        with self.assertLogs("popper", level="INFO") as cm:
            self.assertRaises(SystemExit, ConfigLoader.load, **kwargs)
            self.assertEqual(len(cm.output), 1)
            self.assertTrue("No engine name given" in cm.output[0])

        # resman name missing
        config.update({"engine": {"name": "foo"}})
        with self.assertLogs("popper", level="INFO") as cm:
            self.assertRaises(SystemExit, ConfigLoader.load, **kwargs)
            self.assertEqual(len(cm.output), 1)
            self.assertTrue("No resource manager name given" in cm.output[0])

        # now all OK
        config.update({"resource_manager": {"name": "bar"}})
        conf = ConfigLoader.load(**kwargs)
        self.assertEqual(conf.engine_name, "foo")
        self.assertEqual(conf.resman_name, "bar")
        self.assertEqual(conf.engine_opts, {})
        self.assertEqual(conf.resman_opts, {})

        config.update({"engine": {"name": "bar", "options": {"foo": "baz"}}})
        conf = ConfigLoader.load(**kwargs)
        self.assertEqual(conf.engine_opts, {"foo": "baz"})

    @staticmethod
    def extract_dict(A, B):
        # taken from https://stackoverflow.com/a/21213251
        return dict([(k, B[k]) for k in A.keys() if k in B.keys()])
