import os
import shutil
import time
import unittest

from testfixtures import LogCapture
from subprocess import Popen

import popper.scm as scm
import popper.utils as pu

from popper.config import ConfigLoader
from popper.parser import WorkflowParser
from popper.runner import WorkflowRunner
from popper.runner_kubernetes import DockerRunner, KubernetesRunner
from popper.cli import log as log
from .test_common import PopperTest

import docker

from kubernetes import config, client
from kubernetes.client import Configuration, V1DeleteOptions
from kubernetes.client.api import core_v1_api
from kubernetes.stream import stream

from box import Box


class TestKubernetesRunner(PopperTest):
    def setUp(self):
        log.setLevel("CRITICAL")
        config.load_kube_config()

        c = Configuration()
        c.assert_hostname = False
        Configuration.set_default(c)
        self._kclient = core_v1_api.CoreV1Api()

        _, active_context = config.list_kube_config_contexts()

    def tearDown(self):
        log.setLevel("NOTSET")
        
    @unittest.skipIf(
        os.environ.get("WITH_K8S", "0") != "1"
    )
    def test_vol_claim_create(self):
        repo = self.mk_repo()
        conf = ConfigLoader.load(workspace_dir=repo.working_dir)
        with KubernetesRunner(config=conf) as kr:
            kr._vol_claim_create()
            response = self._kclient.read_namespaced_persistent_volume_claim(
                kr._vol_claim_name, namespace="default"
            )
            self.assertEqual(response.status.phase, "Bound")
            kr._vol_claim_delete()

        repo.close()
        shutil.rmtree(repo.working_dir, ignore_errors=True)
        
    @unittest.skipIf(
        os.environ.get("WITH_K8S", "0") != "1"
    )
    def test_init_pod_create(self):
        repo = self.mk_repo()
        conf = ConfigLoader.load(workspace_dir=repo.working_dir)
        with KubernetesRunner(config=conf) as kr:
            kr._vol_claim_create()
            kr._init_pod_create()
            time.sleep(5)
            response = self._kclient.read_namespaced_pod(
                kr._init_pod_name, namespace="default"
            )
            self.assertEqual(response.status.phase, "Running")
            kr._init_pod_delete()
            kr._vol_claim_delete()

        repo.close()
        shutil.rmtree(repo.working_dir, ignore_errors=True)

    @unittest.skipIf(
        os.environ.get("WITH_K8S", "0") != "1"
    )
    def test_copy_ctx(self):
        repo = self.mk_repo()
        conf = ConfigLoader.load(workspace_dir=repo.working_dir)
        with KubernetesRunner(config=conf) as kr:
            kr._vol_claim_create()
            kr._init_pod_create()
            time.sleep(5)
            response = self._kclient.read_namespaced_pod(
                kr._init_pod_name, namespace="default"
            )
            self.assertEqual(response.status.phase, "Running")
            kr._copy_ctx()
            kr._init_pod_delete()
            kr._vol_claim_delete()

        repo.close()
        shutil.rmtree(repo.working_dir, ignore_errors=True)
