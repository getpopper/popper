import os
import sys
import shutil
import contextlib
import subprocess
from git import Repo

os.environ['test_repo_path'] = '/tmp/mypaper'
os.environ['CI'] = 'false'

pushstack = list()


def pushdir(dirname):
    global pushstack
    pushstack.append(os.getcwd())
    os.chdir(dirname)


def popdir():
    global pushstack
    os.chdir(pushstack.pop())


def delete_dir(path):

    try:
        os.rmdir(path)
    except OSError as e:
        os.system("docker run --rm -v /tmp:/tmp alpine:3.8 rm -rf "+path)


def init_test_repo():

    if(os.environ.get('POPPER_TEST_MODE') == 'with-git'):
        path = os.environ.get('test_repo_path')
        delete_dir(path)
        os.mkdir(path)
        pushdir(path)
        repo = Repo.init(path)
        file = open(path+'/README.md', 'w+')
        file.write("foo")
        repo.git.add(A=True)
        repo.git.commit('-m', 'first')
        popdir()

    else:
        path = os.environ.get('test_repo_path')
        delete_dir(path)
        os.mkdir(path)
        pushdir(path)
        file = open(path+'/README.md', 'w+')
        file.write("foo")
        popdir()
