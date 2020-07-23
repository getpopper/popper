import os
import subprocess
import time
import tarfile

from kubernetes import config, client
from kubernetes.client import Configuration, V1DeleteOptions
from kubernetes.client.api import core_v1_api

from popper import utils as pu
from popper.cli import log as log
from popper.runner import StepRunner as StepRunner
from popper.runner_host import DockerRunner as HostDockerRunner


class KubernetesRunner(StepRunner):
    """Base class for all kubernetes step runners"""

    def __init__(self, **kw):
        super(KubernetesRunner, self).__init__(**kw)

        config.load_kube_config()

        c = Configuration()
        c.assert_hostname = False
        Configuration.set_default(c)
        self._kclient = core_v1_api.CoreV1Api()

        _, active_context = config.list_kube_config_contexts()

        self._namespace = self._config.resman_opts.get("namespace", "default")        

        self._base_pod_name = pu.sanitized_name(f"pod", self._config.wid)
        self._base_pod_name = self._base_pod_name.replace("_", "-")

        self._init_pod_name = pu.sanitized_name("init-pod", self._config.wid)
        self._init_pod_name = self._init_pod_name.replace("_", "-")

        self._vol_claim_name = f"{self._base_pod_name}-pvc"
        self._vol_size = self._config.resman_opts.get("volume_size", "500Mi")

        self._init_pod_created = False
        self._vol_claim_created = False

    def __exit__(self, exc_type, exc_value, exc_traceback):
        super(KubernetesRunner, self).__exit__(exc_type, exc_value, exc_traceback)
        return True

    def run(self, step):
        """Execute a step in a kubernetes cluster."""
        self._pod_name = self._base_pod_name + f"-{step.id}"
        image = self._build_and_push_image(step)

        m = f"[{step.id}] kubernetes run {self._namespace}.{self._pod_name}"
        log.info(m)

        if self._config.dry_run:
            return 0

        ecode = 1
        try:
            self._vol_claim_create()

            if not self._init_pod_created:
                self._init_pod_create()
                self._copy_ctx()
                self._init_pod_delete()
                self._init_pod_created = True

            self._pod_create(step, image)
            self._pod_read_log()
            ecode = self._pod_exit_code()
        except Exception as e:
            log.fail(e)
        finally:
            pass
            # self._pod_delete()
            # self._vol_claim_delete()

        log.debug(f"returning with {ecode}")
        return ecode

    def _build_and_push_image(self, step):
        raise NotImplementedError("Needs implementation in derived class.")

    def stop_running_tasks(self):
        self._pod_delete()

    def _init_pod_create(self):
        """Create a init Pod mounted on a volume with alpine image so that 
        the `tar` utility is available by default and the workflow context 
        can be copied from the local machine into the volume.
        """
        ws_vol_mount = f"{self._init_pod_name}-ws"
        init_pod_conf = {
            "apiVersion": "v1",
            "kind": "Pod",
            "metadata": {"name": self._init_pod_name},
            "spec": {
                "restartPolicy": "Never",
                "containers": [
                    {
                        "image": "alpine:3.11",
                        "name": self._init_pod_name,
                        "workingDir": "/workspace",
                        "command": ["sleep", "infinity"],
                        "volumeMounts": [
                            {"name": ws_vol_mount, "mountPath": "/workspace",}
                        ],
                    }
                ],
                "volumes": [
                    {
                        "name": ws_vol_mount,
                        "persistentVolumeClaim": {"claimName": self._vol_claim_name,},
                    }
                ],
            },
        }

        if self._config.resman_opts.node_selector_host_name:
            init_pod_conf["spec"]["nodeSelector"] = {
                "kubernetes.io/hostname": self._config.resman_opts.node_selector_host_name
            }

        self._kclient.create_namespaced_pod(body=init_pod_conf, namespace=self._namespace)

        # loop and wait for the init pod to come up
        counter = 1
        while True:
            resp = self._kclient.read_namespaced_pod(
                self._init_pod_name, namespace=self._namespace
            )
            if resp.status.phase != "Pending":
                break

            log.debug(f"init pod {self._init_pod_name} not started yet")

            if counter == 10:
                raise Exception("Timed out waiting for init pod to start")

            time.sleep(1)
            counter += 1

    def _copy_ctx(self):
        files = os.listdir(self._config.workspace_dir)
        with tarfile.open("ctx" + ".tar.gz", mode="w:gz") as archive:
            for f in files:
                archive.add(f)

        e = subprocess.call(
            [
                "kubectl",
                "-n",
                self._namespace,
                "cp",
                "ctx.tar.gz",
                f"{self._namespace}/{self._init_pod_name}:/workspace",
            ],
            stdout=subprocess.PIPE,
        )
        if e != 0:
            log.fail("Couldn't copy workspace context into init pod")

        e = subprocess.call(
            [
                "kubectl",
                "exec",
                "-n",
                self._namespace,
                f"{self._init_pod_name}",
                "--",
                "tar",
                "-xvf",
                "/workspace/ctx.tar.gz",
            ],
            stdout=subprocess.PIPE,
        )
        if e != 0:
            log.fail("Unpacking context inside pod failed")

    def _init_pod_delete(self):
        """Teardown the init Pod after the context has been copied
        into the volume.
        """
        log.debug(f"deleting init pod {self._pod_name}")
        self._kclient.delete_namespaced_pod(
            self._init_pod_name, namespace=self._namespace, body=V1DeleteOptions()
        )

    def _vol_claim_create(self):
        """Create a PersistentVolumeClaim to claim usable storage space 
        from a previously created PersistentVolume.
        """
        vol_claim_conf = {
            "apiVersion": "v1",
            "kind": "PersistentVolumeClaim",
            "metadata": {"name": self._vol_claim_name},
            "spec": {
                "storageClassName": "manual",
                "accessModes": ["ReadWriteMany"],
                "resources": {"requests": {"storage": self._vol_size}},
            },
        }

        if self._config.resman_opts.persistent_volume_name:
            vol_claim_conf["spec"][
                "volumeName"
            ] = self._config.resman_opts.persistent_volume_name

        if self._vol_claim_created:
            return

        self._kclient.create_namespaced_persistent_volume_claim(
            namespace=self._namespace, body=vol_claim_conf
        )

        # wait for the volume claim to go into `Bound` state.
        counter = 1
        while True:
            resp = self._kclient.read_namespaced_persistent_volume_claim(
                self._vol_claim_name, namespace=self._namespace
            )
            if resp.status.phase != "Pending":
                break

            log.debug(f"volume claim {self._vol_claim_name} not created yet")

            if counter == 60:
                raise Exception("Timed out waiting for PersistentVolumeClaim creation")

            time.sleep(1)
            counter += 1

        self._vol_claim_created = True

    def _vol_claim_delete(self):
        """Delete the PersistentVolumeClaim.
        """
        log.debug(f"deleting volume claim {self._vol_claim_name}")
        self._kclient.delete_namespaced_persistent_volume_claim(
            self._vol_claim_name, namespace=self._namespace, body=V1DeleteOptions()
        )

    def _pod_create(self, step, image):
        """Start a Pod for each step.
        """
        ws_vol_mount = f"{self._pod_name}-ws"
        pod_conf = {
            "apiVersion": "v1",
            "kind": "Pod",
            "metadata": {"name": self._pod_name},
            "spec": {
                "restartPolicy": "Never",
                "containers": [
                    {
                        "image": image,
                        "name": f"{step.id}",
                        "workingDir": "/workspace",
                        "volumeMounts": [
                            {"name": ws_vol_mount, "mountPath": "/workspace",}
                        ],
                    }
                ],
                "volumes": [
                    {
                        "name": ws_vol_mount,
                        "persistentVolumeClaim": {"claimName": self._vol_claim_name,},
                    }
                ],
            },
        }

        if self._config.resman_opts.node_selector_host_name:
            pod_conf["spec"]["nodeSelector"] = {
                "kubernetes.io/hostname": self._config.resman_opts.node_selector_host_name
            }

        runs = list(step.runs) if step.runs else None
        args = list(step.args) if step.args else None

        if runs:
            pod_conf["spec"]["containers"][0]["command"] = runs

        if args:
            pod_conf["spec"]["containers"][0]["args"] = args

        self._kclient.create_namespaced_pod(body=pod_conf, namespace=self._namespace)

        counter = 1
        while True:
            resp = self._kclient.read_namespaced_pod(
                self._pod_name, namespace=self._namespace
            )
            if resp.status.phase != "Pending":
                break

            log.debug(f"pod {self._pod_name} not started yet")

            if counter == self._config.resman_opts.timeoutRetryLimit:
                raise Exception("Timed out waiting for Pod to start")

            time.sleep(1)
            counter += 1

    def _pod_read_log(self):
        """Read logs from the Pod after it moves into `Completed` state.
        """
        log.debug(f"reading logs from {self._pod_name}")
        resp = self._kclient.read_namespaced_pod_log(
            name=self._pod_name,
            namespace=self._namespace,
            follow=True,
            tail_lines=10,
            _preload_content=False,
        )
        for line in resp:
            log.step_info(line.decode().rstrip())

    def _pod_exit_code(self):
        """Read the exit code from the Pod to decide the exit code of the step.
        """
        time.sleep(2)
        resp = self._kclient.read_namespaced_pod(
            name=self._pod_name, namespace=self._namespace
        )
        log.debug(f"got status {resp.status.phase}")
        if resp.status.phase != "Succeeded":
            return 1
        return 0

    def _pod_delete(self):
        """Delete the Pod after it has moved into `Completed` state.
        """
        log.debug(f"deleting pod {self._pod_name}")
        self._kclient.delete_namespaced_pod(
            self._pod_name, namespace=self._namespace, body=V1DeleteOptions()
        )


class DockerRunner(KubernetesRunner, HostDockerRunner):
    """Runs steps on kubernetes; builds images locally using docker.
    """

    def __init__(self, **kw):
        super(DockerRunner, self).__init__(**kw)

    def _build_and_push_image(self, step):
        needs_build, img, tag, build_ctx_path = self._get_build_info(step)
        if not needs_build:
            return step.uses.replace("docker://", "")

        if not self._config.resman_opts.registry:
            raise Exception("Expecting 'registry' option in configuration.")

        img = img.replace("/", "_")
        img = f"{self._config.resman_opts.registry}/{self._config.resman_opts.registry_user}/{img}"

        self._d.images.build(
            path=build_ctx_path, tag=f"{img}:{tag}", rm=True, pull=True
        )

        for l in self._d.images.push(img, tag=tag, stream=True, decode=True):
            log.step_info(l)

        log.debug(f"image built {img}:{tag}")
        return f"{img}:{tag}"
