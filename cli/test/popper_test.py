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

    def check_output(self, command, actions):

    	result = subprocess.Popen(command, stdout = subprocess.PIPE)
    	output = str(result.communicate())

    	if("ERROR" in output):
    		if(excepted_output == 0):
    			output = output.split('\n')
    			output = output[0].split('\\')
    			result = []

    			for line in output :
    				result.append(line)

    			for i in range(1, len(result)-1):
    				print(result[i])

    			return 1

    		else:
    			return 0

    	elif(all(x in output for x in actions)):
    		return 0

    	else:
    		return 1
