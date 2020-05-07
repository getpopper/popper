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

    def test_get_remote_url(self):
        repo = self.mk_repo()
        url = scm.get_remote_url(repo)
        self.assertEqual(url, "https://github.com/my/repo")

        self.assertEqual(scm.get_remote_url(None), "")

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
