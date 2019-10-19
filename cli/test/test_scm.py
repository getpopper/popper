import os
import sys
import shutil
import unittest

import git

from popper import scm
from popper.cli import log


class TestScm(unittest.TestCase):
    """Unit tests for popper.scm module.
    """

    def setUp(self):
        if os.environ.get('POPPER_TEST_MODE') == 'with-git':
            self.with_git = True
        else:
            self.with_git = False

        log.setLevel('CRITICAL')
        if os.path.exists('/tmp/test_folder'):
            shutil.rmtree('/tmp/test_folder')
        os.makedirs('/tmp/test_folder')
        os.chdir('/tmp/test_folder')
        scm.clone(
            'https://github.com',
            'popperized',
            'github-actions-demo',
            os.path.join(os.getcwd(), 'github-actions-demo')
        )
        if not self.with_git:
            shutil.rmtree('/tmp/test_folder/github-actions-demo/.git')
        os.chdir('/tmp/test_folder/github-actions-demo')

    def tearDown(self):
        log.setLevel('NOTSET')
        os.chdir('/tmp')
        shutil.rmtree('/tmp/test_folder')

    def test_get_git_root_folder(self):
        root_folder = scm.get_git_root_folder()
        self.assertEqual(
            root_folder,
            '/tmp/test_folder/github-actions-demo')

    def test_get_name(self):
        name = scm.get_name()
        self.assertEqual(name, 'github-actions-demo')

    def test_get_user(self):
        user = scm.get_user()
        if self.with_git:
            self.assertEqual(user, 'popperized')
        else:
            self.assertEqual(user, '')

    def test_get_remote_url(self):
        url = scm.get_remote_url()
        if self.with_git:
            self.assertEqual(
                url, 'https://github.com/popperized/github-actions-demo')
        else:
            self.assertEqual(url, '')

    def test_get_ref(self):
        ref = scm.get_ref()
        if self.with_git:
            self.assertEqual(ref, 'refs/heads/master')
        else:
            self.assertEqual(ref, 'unknown')

    def test_get_sha(self):
        sha = scm.get_sha()
        if self.with_git:
            self.assertEqual(sha, '9ec4d31')
        else:
            self.assertEqual(sha, 'unknown')

    def test_get_head_commit(self):
        head_commit_object = scm.get_head_commit()
        if self.with_git:
            hexsha = head_commit_object.hexsha
            self.assertEqual(
                hexsha, '9ec4d316eb8da32a5e7153309464aa8fb8b0803a')
        else:
            self.assertIsNone(head_commit_object)

    def test_get_git_files(self):
        files = scm.get_git_files()
        if self.with_git:
            self.assertListEqual(files, [
                '.github/actions/jshint/Dockerfile',
                '.github/main.workflow',
                '.gitignore',
                'LICENSE',
                'README.md',
                'index.js',
                'package-lock.json',
                'package.json', 'tests/test-app.js'
            ])
        else:
            self.assertIsNone(files)

    def test_clone(self):
        os.makedirs('/tmp/test_folder/test_clone')
        os.chdir('/tmp/test_folder/test_clone')
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
