import os
import sys
import shutil
import contextlib
import subprocess
from git import Repo


class PopperTest:

    def __init__(self):

        self.test_repo_path = '/tmp/mypaper'
        self.ci = False

    def delete_dir(self, path):

        try:
            os.rmdir(path)
        except OSError as e:
            os.system("docker run --rm -v /tmp:/tmp alpine:3.8 rm -rf "+path)

    def init_test_repo(self):

        path = self.test_repo_path
        delete_dir(path)
        os.mkdir(path)
        file = open(path+'/README.md', 'w+')
        file.write("foo")
