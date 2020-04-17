import os
import sys
import shutil
import contextlib
import subprocess
import tempfile
import git
import unittest

FIXDIR = f'{os.path.dirname(os.path.realpath(__file__))}/fixtures'


class PopperTest:

    def mk_repo(self):
        """creates a test repo in a random temp file. Equivalent to:
        REPODIR=/tmp/<random>
        mkdir $REPODIR
        cd $REPODIR
        git init
        touch README.md
        git add .
        git commit -m 'first commit'
        """
        tempdir = tempfile.mkdtemp()
        repo = git.Repo.init(tempdir)
        readme = os.path.join(tempdir, 'README.md')
        open(readme, 'w').close()
        repo.index.add([readme])
        repo.index.commit('first commit')
        return repo

class PopperCommonTest(unittest.TestCase, PopperTest):

    def test_mkrepo(self):

        repo = self.mk_repo()
        self.assertTrue(os.path.isdir(repo.working_tree_dir))
        self.assertTrue(os.path.isfile(os.path.join(repo.working_tree_dir, 'README.md')))
