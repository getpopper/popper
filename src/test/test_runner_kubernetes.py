import os
import shutil
import time
import unittest

import popper.scm as scm
import popper.utils as pu

from popper.config import ConfigLoader
from popper.runner import WorkflowRunner
from popper.runner_kubernetes import KubernetesRunner
from popper.cli import log as log
from .test_common import PopperTest

from kubernetes import config, client
from kubernetes.client import Configuration, V1DeleteOptions
from kubernetes.client.api import core_v1_api
from kubernetes.stream import stream

from box import Box


@unittest.skipIf(
    os.environ.get("ENABLE_K8S_RUNNER_TESTS", "0") != "1",
    "Kubernetes runner tests not enabled.",
)
class TestKubernetesRunner(PopperTest):
    def setUp(self):
        log.setLevel("CRITICAL")
        config.load_kube_config()

        c = Configuration()
        c.assert_hostname = False
        Configuration.set_default(c)
        self._kclient = core_v1_api.CoreV1Api()

        config.list_kube_config_contexts()

    def tearDown(self):
        log.setLevel("NOTSET")

    def test_vol_claim_create_delete(self):
        repo = self.mk_repo()
        conf = ConfigLoader.load(workspace_dir=repo.working_dir)
        with KubernetesRunner(config=conf) as kr:
            kr._vol_claim_create()
            response = self._kclient.read_namespaced_persistent_volume_claim(
                kr._vol_claim_name, namespace="default"
            )
            self.assertEqual(response.status.phase, "Bound")
            kr._vol_claim_delete()
            self.assertRaises(
                Exception,
                self._kclient.read_namespaced_persistent_volume_claim,
                {"name": kr._vol_claim_name, "namespace": "default"},
            )

        repo.close()
        shutil.rmtree(repo.working_dir, ignore_errors=True)

    def test_init_pod_create_delete(self):
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
            self.assertRaises(
                Exception,
                self._kclient.read_namespaced_pod,
                **{"name": kr._init_pod_name, "namespace": "default"},
            )

        repo.close()
        shutil.rmtree(repo.working_dir, ignore_errors=True)

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

    def test_pod_create_delete_exitcode(self):
        repo = self.mk_repo()
        conf = ConfigLoader.load(workspace_dir=repo.working_dir)
        with KubernetesRunner(config=conf) as kr:
            kr._vol_claim_create()
            step = Box(
                {
                    "id": "test",
                    "uses": "docker://alpine:3.9",
                    "runs": ("echo", "hello"),
                },
                default_box=True,
            )
            kr._pod_name = kr._base_pod_name + f"-{step.id}"
            kr._pod_create(step, "alpine:3.9")
            self.assertEqual(kr._pod_exit_code(), 0)
            response = self._kclient.read_namespaced_pod(
                kr._pod_name, namespace="default"
            )
            self.assertEqual(response.status.phase, "Succeeded")
            kr._pod_delete()
            self.assertRaises(
                Exception,
                self._kclient.read_namespaced_pod,
                **{"name": kr._pod_name, "namespace": "default"},
            )

            time.sleep(5)

            step = Box(
                {
                    "id": "test",
                    "uses": "docker://alpine:3.9",
                    "runs": ("ecdho", "hello"),
                },
                default_box=True,
            )
            kr._pod_name = kr._base_pod_name + f"-{step.id}"
            kr._pod_create(step, "alpine:3.9")
            self.assertEqual(kr._pod_exit_code(), 1)
            response = self._kclient.read_namespaced_pod(
                kr._pod_name, namespace="default"
            )
            self.assertEqual(response.status.phase, "Failed")
            kr._pod_delete()
            kr._vol_claim_delete()

            self.assertRaises(
                Exception,
                self._kclient.read_namespaced_pod,
                **{"name": kr._pod_name, "namespace": "default"},
            )
