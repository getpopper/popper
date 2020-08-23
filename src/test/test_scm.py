import os
import tempfile

import git

from popper import scm
from popper.cli import log

from .test_common import PopperTest


class TestScm(PopperTest):
    @classmethod
    def setUpClass(self):
        log.setLevel("CRITICAL")

    @classmethod
    def tearDownClass(self):
        log.setLevel("NOTSET")

    def test_empty_repo(self):
        tempdir = tempfile.mkdtemp()
        repo = git.Repo.init(tempdir)
        self.assertTrue(scm.is_empty(repo))

        self.assertIsNone(scm.get_sha(repo))
        self.assertIsNone(scm.get_branch(repo))
        self.assertIsNone(scm.get_tag(repo))

        repo = self.mk_repo()
        self.assertFalse(scm.is_empty(repo))

    def test_get_remote_url(self):
        repo = self.mk_repo()
        url = scm.get_remote_url(repo)
        self.assertEqual(url, "https://github.com/my/repo")

        self.assertEqual(scm.get_remote_url(None), "")

    def test_get_branch_in_detached_head_state(self):
        repo = self.mk_repo()

        repo.git.checkout("HEAD~1")

        os.environ["TRAVIS_BRANCH"] = "travis"
        self.assertEqual("travis", scm.get_branch(repo))
        os.environ.pop("TRAVIS_BRANCH")

        os.environ["GIT_BRANCH"] = "jenkins"
        self.assertEqual("jenkins", scm.get_branch(repo))
        os.environ.pop("GIT_BRANCH")

        os.environ["CIRCLE_BRANCH"] = "circle"
        self.assertEqual("circle", scm.get_branch(repo))
        os.environ.pop("CIRCLE_BRANCH")

        os.environ["CI_COMMIT_REF_NAME"] = "gitlab"
        self.assertEqual("gitlab", scm.get_branch(repo))
        os.environ.pop("CI_COMMIT_REF_NAME")

        self.assertEqual(scm.get_sha(repo), scm.get_branch(repo))

        # None given as arg
        self.assertIsNone(scm.get_sha(None))
        self.assertIsNone(scm.get_sha(None, short=8))
        self.assertIsNone(scm.get_branch(None))

    def test_get_tag(self):
        self.assertIsNone(scm.get_tag(None))

        repo = self.mk_repo()
        repo.git.checkout("HEAD~1")

        os.environ["TRAVIS_TAG"] = "travis"
        self.assertEqual("travis", scm.get_tag(repo))
        os.environ.pop("TRAVIS_TAG")

        os.environ["GIT_TAG"] = "jenkins"
        self.assertEqual("jenkins", scm.get_tag(repo))
        os.environ.pop("GIT_TAG")

        os.environ["CIRCLE_TAG"] = "circle"
        self.assertEqual("circle", scm.get_tag(repo))
        os.environ.pop("CIRCLE_TAG")

        os.environ["CI_COMMIT_REF_NAME"] = "gitlab"
        self.assertEqual("gitlab", scm.get_tag(repo))
        os.environ.pop("CI_COMMIT_REF_NAME")

        # without any of the above, it should be empty
        self.assertIsNone(scm.get_tag(repo))

        # test with a tagged commit
        repo = self.mk_repo(tag="foo")
        self.assertEqual("foo", scm.get_tag(repo))

    def test_clone(self):
        tempdir = tempfile.mkdtemp()
        tdir = os.path.join(tempdir, "test_clone")
        os.makedirs(tdir)
        currdir = os.getcwd()
        os.chdir(tdir)
        scm.clone(
            "https://github.com",
            "popperized",
            "github-actions-demo",
            os.path.join(os.getcwd(), "gad"),
            "develop",
        )
        repo = git.Repo(os.path.join(os.getcwd(), "gad"))
        self.assertEqual(repo.active_branch.name, "develop")
        scm.clone(
            "https://github.com",
            "popperized",
            "github-actions-demo",
            os.path.join(os.getcwd(), "gad"),
            "master",
        )
        repo = git.Repo(os.path.join(os.getcwd(), "gad"))
        self.assertEqual(repo.active_branch.name, "master")
        repo.close()
        os.chdir(currdir)

    def test_parse(self):
        test_url = "ssh://git@github.com:popperized" "/github-actions-demo.git"
        self.assertRaises(SystemExit, scm.parse, test_url)
        test_url = "https://github.com/popperized@master"
        self.assertRaises(SystemExit, scm.parse, test_url)
        test_url = "github.com"
        self.assertRaises(SystemExit, scm.parse, test_url)
        test_url = "@master"
        self.assertRaises(SystemExit, scm.parse, test_url)
        test_url = "http://gitlab.com/popperized/github-actions-demo.git"
        parts = scm.parse(test_url)
        self.assertTupleEqual(
            parts,
            (
                "http://gitlab.com",
                "gitlab.com",
                "popperized",
                "github-actions-demo",
                "",
                None,
            ),
        )
        test_url = "https://github.com/popperized" "/github-actions-demo@master"
        parts = scm.parse(test_url)
        self.assertTupleEqual(
            parts,
            (
                "https://github.com",
                "github.com",
                "popperized",
                "github-actions-demo",
                "",
                "master",
            ),
        )
        test_url = "github.com/popperized/github-actions-demo"
        parts = scm.parse(test_url)
        self.assertTupleEqual(
            parts,
            (
                "https://github.com",
                "github.com",
                "popperized",
                "github-actions-demo",
                "",
                None,
            ),
        )
        test_url = "popperized/github-actions-demo/path/to/action@develop"
        parts = scm.parse(test_url)
        self.assertTupleEqual(
            parts,
            (
                "https://github.com",
                "github.com",
                "popperized",
                "github-actions-demo",
                "path/to/action",
                "develop",
            ),
        )
