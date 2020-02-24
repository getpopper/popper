import os
import tempfile
import shutil

import git


def clone_repo(url, path, with_git=True):
    """clones the given repo url into given path and returns a git.Repo object.
    If with_git is False, it removes the .git/ folder before returning."""
    repourl = 'https://github.com/popperized/bin'
    repo = git.Repo.clone_from(repourl, path)
    if not with_git:
        shutil.rmtree(os.path.join(path, '.git'))
    return repo


def mk_repo():
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
