import os
import tempfile
import git
import unittest


class PopperTest(unittest.TestCase):
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

        # touch README file
        readme = os.path.join(tempdir, "README.md")
        open(readme, "w").close()

        # create first commit
        repo.index.add([readme])
        repo.index.commit("first commit")

        # create second commit
        with open(readme, "w") as f:
            f.write("README content\n")
        repo.index.add([readme])
        repo.index.commit("second commit")

        # create a remote
        repo.create_remote("origin", url="https://github.com/my/repo")

        return repo


class PopperCommonTest(PopperTest):
    def test_mkrepo(self):

        repo = self.mk_repo()
        self.assertTrue(os.path.isdir(repo.working_tree_dir))
        self.assertTrue(
            os.path.isfile(os.path.join(repo.working_tree_dir, "README.md"))
        )
