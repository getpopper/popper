import os
import unittest

from popper.cli import log as log
from popper.config import PopperConfig
from popper.parser import YMLWorkflow
from popper.runner import WorkflowRunner
from popper.runner_kubernetes import KubernetesRunner, DockerRunner

from .test_common import PopperTest


class TestKubernetesDockerRunner(PopperTest):
    def setUp(self):
        log.setLevel('CRITICAL')

    @unittest.skipIf(
        not os.environ.get('WITH_K8S', None) or
        os.environ.get('ENGINE', 'docker') != 'docker',
        'WITH_K8S not defined or ENGINE != docker')
    def test_docker_build_image(self):
        repo = self.mk_repo()

        # NOTE: if you are testing locally and you are not authorized to push
        #       to the popperized repository, then you need to change this
        #       with the your docker.io username so that the test can pass.
        config_opts = {
            'registry_user': 'edeediong',
        }
        conf = PopperConfig(workspace_dir=repo.working_dir,
                            resman_name='kubernetes',
                            config_file=config_opts)

        with WorkflowRunner(conf) as r:
            wf = YMLWorkflow("""
            version: '1'
            steps:
            - uses: 'popperized/bin/sh@master'
              runs: [cat]
              args: README.md
            """)
            wf.parse()

            # this should cause a container to be built locally,
            # pushed to the popperized/bin repo, and then the image
            # be pulled by kubernetes when setting up the pod
            r.run(wf)

    @unittest.skipIf(
        not os.environ.get('WITH_K8S', None) or
        os.environ.get('ENGINE', 'docker') != 'docker',
        'WITH_K8S not defined or ENGINE != docker')
    def test_docker_write_to_volume(self):
        repo = self.mk_repo()
        config_opts = {
            'registry_user': 'edeediong',
        }
        conf = PopperConfig(workspace_dir=repo.working_dir,
                            resman_name='kubernetes', config_file=config_opts)

        with WorkflowRunner(conf) as r:

            wf = YMLWorkflow("""
            version: '1'
            steps:
            - uses: 'docker://alpine:3.9'
              runs: ['sh', '-c', 'echo $FOO > hello.txt ; pwd']
              env: {
                  FOO: bar
              }
            """)
            wf.parse()
            r.run(wf)

            # TODO: use kubernetes client to assert that the file was
            #       created in the volume associated to the pod

            with open(os.path.join(repo.working_dir, 'hello.txt'), 'r') as f:
                self.assertEqual(f.read(), 'bar\n')

        repo.close()
