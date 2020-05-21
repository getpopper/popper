from click.testing import CliRunner

from popper.config import ConfigLoader
import popper.commands.cmd_run as run
from .test_common import PopperTest
#from popper.parser import YMLWorkflow, HCLWorkflow
from popper.runner import WorkflowRunner
from popper.parser import WorkflowParser

import docker
import unittest
import os
import tempfile
import git
import re
import tarfile
import logging
import sys

class TestReuse(PopperTest):

	def test_reuse(self):

		import os
		import hashlib
		identifier = str(os.getuid()) + "_main.yaml"
		id_val = str(hashlib.md5(identifier.encode()).hexdigest())

		repo = self.mk_repo()
		conf = ConfigLoader.load(workspace_dir=repo.working_dir)

		with self.assertLogs('popper') as test_logger:
			with WorkflowRunner(conf) as r:

				wf_data = {
					"steps": [
						{
							"uses": 'popperized/bin/sh@master',
		              		"args": ['ls'],
						}
					]
				}

				r.run(WorkflowParser.parse(wf_data=wf_data))


				client = docker.from_env()
				container_list = client.containers.list(all=True)
				req_containers = [x for x in container_list if re.search('popper_1', x.name)]

				self.assertGreater(len(req_containers),0)

				req_container = req_containers[0]

				os.system('docker cp cli/test/fixtures/reuse.yaml ' + req_container.name + ':/')


		conf = ConfigLoader.load(workspace_dir=repo.working_dir, reuse=True)

		with WorkflowRunner(conf) as r:

			wf_data = {
				"steps": [
					{
						"uses": 'popperized/bin/sh@master',
		              	"args": ['ls'],
					}
				]
			}

			r.run(WorkflowParser.parse(wf_data=wf_data))

		conf = ConfigLoader.load(workspace_dir=repo.working_dir)

		with WorkflowRunner(conf) as r:

			wf_data = {
				"steps": [
					{
						"uses": 'popperized/bin/sh@master',
		              	"args": ['ls', '-a'],
					}
				]
			}

			r.run(WorkflowParser.parse(wf_data=wf_data))





	# 	with WorkflowRunner(conf) as r:

	# 		wf = YMLWorkflow("""
 #            version: '1'
 #            steps:
 #            - uses: 'popperized/bin/sh@master'
 #              args: ['ls']
 #            """)

	# 		wf.parse()
	# 		r.run(wf)

	# 		client = docker.from_env()
	# 		container_list = client.containers.list(all= True)
	# 		print(id_val)
	# 		output = [x for x in container_list if re.search('popper_1', x.name)]

	# 		self.assertGreater(len(output),0)
	# 		os.system('docker cp cli/test/fixtures/reuse.yaml ' + output[0].name + ':/')
			
	# 	# runner = CliRunner()
	# 	# result = runner.invoke(run.cli, ['--wfile', 'cli/test/fixtures/reuse.yaml', '--reuse'])
	# 	# assert result.exit_code == 0

	# 	# os.system('docker cp '+ output[0] +':/reuse.yaml reuse-new.yaml')

	# 	# runner = CliRunner()
	# 	# result = runner.invoke(run.cli, ['--wfile', 'reuse-new.yaml'])
	# 	# assert result.exit_code == 0


	# @unittest.skipIf(os.environ['ENGINE'] == 'singularity', 'ENGINE == singularity')
	# def test_nonsingularity(self):

	# 	repo = self.mk_repo()
	# 	conf = ConfigLoader(workspace_dir = repo.working_dir)

	# 	logger.setLevel(os.environ.get('LOG_LEVEL', logging.STEP_INFO))
	# 	with self.assertLogs('popper') as test_logger:
	# 		with WorkflowRunner(conf) as r:

	# 			wf = YMLWorkflow("""
 #                    version: '1'
 #                    steps:
 #                    - uses: 'popperized/bin/sh@master'
 #                      args: ['ls']
 #                      env: {MESSAGE : 'message in a bottle'}
 #                    """)

	# 		wf.parse()
	# 		r.run(wf)

	# 	print("output", test_logger.output)

	# 	runner = CliRunner()
	# 	result = runner.invoke(run.cli, ['--wfile','cli/test/fixtures/reuse.yaml'])
	# 	assert  result.exit_code == 0


		# with self.assertLogs("popper") as test_logger:
		# 	with WorkflowRunner(conf) as r:

		# 		wf = YMLWorkflow("""
	 #            version: '1'
	 #            steps:
	 #            - uses: 'popperized/bin/sh@master'
	 #              args: ['ls']
	 #              env: {MESSAGE : 'message in a bottle'}
	 #            """)

		# 		wf.parse()
		# 		r.run(wf)

		# print("output", test_logger.output)


		# with WorkflowRunner(conf) as r:

		# 	wf = YMLWorkflow("""
		# 		version: '1'
	 #            steps:
	 #            - uses: 'popperized/bin/sh@master'
	 #              runs : ['sh', '-c','echo $MESSAGE']""")

		# 	wf.parse()
		# 	r.run(wf)

		# with WorkflowRunner(conf) as r:

		# 	wf = YMLWorkflow("""
		# 		version: '1'
	 #            steps:
	 #            - uses: 'popperized/bin/sh@master'
	 #              runs : ['sh', '-c','echo "Hello from Popper 2.x !" > /usr/local/popper.file']""")

		# 	wf.parse()
		# 	r.run(wf)

		# with WorkflowRunner(conf) as r:

		# 	wf = YMLWorkflow("""
		# 		version: '1'
	 #            steps:
	 #            - uses: 'popperized/bin/sh@master'
	 #              runs : ['sh', '-c','cat /usr/local/popper.file']""")

		# 	wf.parse()
		# 	r.run(wf)






#logging.basicConfig(stream=sys.stderr, level=15)


