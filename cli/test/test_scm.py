import os
import shutil
import tempfile
import unittest

import git

from popper import scm
from popper.cli import log


class TestScm(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        log.setLevel('CRITICAL')

        self.tempdir = tempfile.mkdtemp()
        self.curr_dir = os.getcwd()

        self.repo = git.Repo.clone_from('https://github.com/popperized/bin',
                                        os.path.join(self.tempdir, 'bin'))

        self.repodir = os.path.join(self.tempdir, 'bin')

        os.chdir(self.repodir)

        self.gitdir = os.path.join(self.repodir, '.git')
        self.gotdor = os.path.join(self.repodir, '.got')

    @classmethod
    def tearDownClass(self):
        log.setLevel('NOTSET')

        # return to where we were before this test
        os.chdir(self.curr_dir)

        self.repo.close()

    def test_with_git(self):

        if not os.path.exists(self.gitdir):
            shutil.move(self.gotdor, self.gitdir)

        # root folder
        root_folder = scm.get_project_root_folder(self.repo)
        self.assertEqual(os.path.realpath(root_folder),
                         os.path.realpath(os.path.join(self.tempdir, 'bin')))

        # get_remote_url
        url = scm.get_remote_url(self.repo)
        auth_token = os.getenv('GITHUB_API_TOKEN')
        if not auth_token:
            self.assertEqual(url, 'https://github.com/popperized/bin')
        else:
            self.assertTrue('github.com/popperized/bin' in url)

        # get sha
        sha = scm.get_sha(self.repo)
        expected = self.repo.git.rev_parse(self.repo.head.object.hexsha,
                                           short=True)
        self.assertEqual(sha, expected)

    def test_without_git(self):
        shutil.move(self.gitdir, self.gotdor)

        # root folder
        root_folder = scm.get_project_root_folder(None)
        self.assertEqual(os.path.realpath(root_folder),
                         os.path.realpath(os.path.join(self.tempdir, 'bin')))

        # get_remote_url
        self.assertEqual(scm.get_remote_url(None), '')

        # get sha
        sha = scm.get_sha(None)
        self.assertEqual(sha, 'na')

    def test_clone(self):
        tdir = os.path.join(self.tempdir, 'test_clone')
        os.makedirs(tdir)
        currdir = os.getcwd()
        os.chdir(tdir)
        scm.clone(
            'https://github.com',
            'popperized',
            'github-actions-demo',
            os.path.join(os.getcwd(), 'gad'),
            'develop'
        )
        repo = git.Repo(os.path.join(os.getcwd(), 'gad'))
        self.assertEqual(repo.active_branch.name, 'develop')
        scm.clone(
            'https://github.com',
            'popperized',
            'github-actions-demo',
            os.path.join(os.getcwd(), 'gad'),
            'master'
        )
        repo = git.Repo(os.path.join(os.getcwd(), 'gad'))
        self.assertEqual(repo.active_branch.name, 'master')
        repo.close()
        os.chdir(currdir)

    def test_parse(self):
        test_url = ("ssh://git@github.com:popperized"
                    "/github-actions-demo.git")
        self.assertRaises(SystemExit, scm.parse, test_url)
        test_url = "https://github.com/popperized@master"
        self.assertRaises(SystemExit, scm.parse, test_url)
        test_url = "github.com"
        self.assertRaises(SystemExit, scm.parse, test_url)
        test_url = "@master"
        self.assertRaises(SystemExit, scm.parse, test_url)
        test_url = "http://gitlab.com/popperized/github-actions-demo.git"
        parts = scm.parse(test_url)
        self.assertTupleEqual(parts, (
            'http://gitlab.com',
            'gitlab.com',
            'popperized',
            'github-actions-demo',
            '', None))
        test_url = ("https://github.com/popperized"
                    "/github-actions-demo@master")
        parts = scm.parse(test_url)
        self.assertTupleEqual(parts, (
            'https://github.com',
            'github.com',
            'popperized',
            'github-actions-demo',
            '',
            'master'))
        test_url = "github.com/popperized/github-actions-demo"
        parts = scm.parse(test_url)
        self.assertTupleEqual(parts, (
            'https://github.com',
            'github.com',
            'popperized',
            'github-actions-demo',
            '',
            None))
        test_url = "popperized/github-actions-demo/path/to/action@develop"
        parts = scm.parse(test_url)
        self.assertTupleEqual(parts, (
            'https://github.com',
            'github.com',
            'popperized',
            'github-actions-demo',
            'path/to/action',
            'develop'))
