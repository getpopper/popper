import os
import sys
import shutil
import contextlib
import subprocess
import tempfile
import git

FIXDIR = f'{os.path.dirname(os.path.realpath(__file__))}/fixtures'


class PopperTest:

    def __init__(self):

        self.test_repo_path = '/tmp/mypaper'
        self.ci = False

    def delete_dir(self, path):

        try:
            os.rmdir(path)
        except OSError as e:
            os.system("docker run --rm -v /tmp:/tmp alpine:3.8 rm -rf "+path)

    def _wfile(self, name, format):
        return f'{FIXDIR}/{name}.{format}'

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
