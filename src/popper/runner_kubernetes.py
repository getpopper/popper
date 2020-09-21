import os
import base64
import time
import tarfile

from kubernetes import config, client
from kubernetes.client import Configuration, V1DeleteOptions
from kubernetes.client.rest import ApiException
from kubernetes.client.api import core_v1_api
from kubernetes.stream import stream

from popper import utils as pu
from popper.cli import log as log
from popper.runner import StepRunner as StepRunner
from popper.runner_host import DockerRunner as HostDockerRunner


class KubernetesRunner(StepRunner):
    """Runs steps on a kubernetes cluster."""

    def __init__(self, **kw):
        super(KubernetesRunner, self).__init__(**kw)

        config.load_kube_config()

        c = Configuration()
        c.assert_hostname = False
        Configuration.set_default(c)
        self._kclient = core_v1_api.CoreV1Api()

        config.list_kube_config_contexts()

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

        needs_build, _, img, tag, _ = self._get_build_info(step)

        if needs_build:
            log.fail(f"Cannot build ")

        image = f"{img}:{tag}"

        m = f"[{step.id}] kubernetes run {self._namespace}.{self._pod_name}"
        log.info(m)

        if self._config.dry_run:
            return 0

        ecode = 1
        try:
            if not self._vol_claim_created:
                if not self._vol_claim_exists():
                    self._vol_claim_create()
                self._vol_claim_created = True

            if not self._init_pod_created:
                e, self._pod_host_node = self._init_pod_schedule()
                if e:
                    raise Exception("None of the nodes are schedulable.")
                self._copy_ctx()
                self._init_pod_delete()
                self._init_pod_created = True

            self._pod_create(step, image, self._pod_host_node)
            self._pod_read_log()
            ecode = self._pod_exit_code()
        except Exception as e:
            log.fail(e)
        finally:
            self._pod_delete()

        log.debug(f"returning with {ecode}")
        return ecode

    def stop_running_tasks(self):
        """Delete the Pod and then the PersistentVolumeClaim upon receiving SIGINT.
        """
        log.debug("received SIGINT. deleting pod and volume claim")
        self._pod_delete()

    def _init_pod_schedule(self):
        """If a node selector is not provided, select a node randomly
        and stick to it."""
        e = 0
        pod_host_node = None

        if self._config.resman_opts.get("pod_host_node", None):
            e = self._init_pod_create(self._config.resman_opts.pod_host_node)
            pod_host_node = self._config.resman_opts.pod_host_node

        elif not self._config.resman_opts.get("persistent_volume_name", None):
            nodes = [
                node.metadata.labels["kubernetes.io/hostname"]
                for node in self._kclient.list_node().items
            ]
            for node in nodes:
                log.debug(f"trying to schedule init pod on {node}")
                e = self._init_pod_create(node)
                if not e:
                    pod_host_node = node
                    break
                else:
                    self._init_pod_delete()
        else:
            e = self._init_pod_create()
            pod_host_node = None

        return e, pod_host_node

    def _copy_ctx(self):
        """Tar up the workspace context and copy the tar file into
        the PersistentVolume in the Pod.
        """
        files = os.listdir(self._config.workspace_dir)
        with tarfile.open(
            os.path.join(self._config.workspace_dir, "ctx.tar.gz"), mode="w:gz"
        ) as archive:
            for f in files:
                archive.add(f)

        exec_command = ["/bin/sh"]
        response = stream(
            self._kclient.connect_get_namespaced_pod_exec,
            self._init_pod_name,
            self._namespace,
            command=exec_command,
            stderr=True,
            stdin=True,
            stdout=True,
            tty=False,
            _preload_content=False,
        )

        source_file = os.path.join(self._config.workspace_dir, "ctx.tar.gz")
        destination_file = "/workspace/ctx.tar.gz"

        with open(source_file, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read())

        commands = [
            f"echo {encoded_string.decode('utf-8')} | base64 --decode > {destination_file}"
        ]

        while response.is_open():
            response.update(timeout=1)
            if response.peek_stdout():
                log.debug(f"stdout: {response.read_stdout()}")
            if response.peek_stderr():
                log.debug(f"stderr: {response.read_stderr()}")
            if commands:
                c = commands.pop(0)
                log.debug(f"running command... {c}")
                response.write_stdin(c)
            else:
                break
        response.close()

        # extract the archive inside the pod
        exec_command = ["tar", "-zxvf", "/workspace/ctx.tar.gz"]
        response = stream(
            self._kclient.connect_get_namespaced_pod_exec,
            self._init_pod_name,
            self._namespace,
            command=exec_command,
            stderr=True,
            stdin=False,
            stdout=True,
            tty=False,
        )

        log.debug(response)

    def _init_pod_create(self, pod_host_node=None):
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
                        "image": "debian:stable",
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

        if pod_host_node:
            init_pod_conf["spec"]["nodeSelector"] = {
                "kubernetes.io/hostname": pod_host_node
            }

        self._kclient.create_namespaced_pod(
            body=init_pod_conf, namespace=self._namespace
        )

        # loop and wait for the init pod to come up
        counter = 1
        while True:
            response = self._kclient.read_namespaced_pod(
                self._init_pod_name, namespace=self._namespace
            )
            if response.status.phase != "Pending":
                break

            log.debug(f"init pod {self._init_pod_name} not started yet")

            if counter == self._config.resman_opts.get("pod_retry_limit", 60):
                return 1

            time.sleep(1)
            counter += 1

        return 0

    def _init_pod_delete(self):
        """Teardown the init Pod after the context has been copied
        into the volume.
        """
        log.debug(f"deleting init pod {self._init_pod_name}")
        self._kclient.delete_namespaced_pod(
            self._init_pod_name, namespace=self._namespace, body=V1DeleteOptions()
        )

    def _vol_create(self, volume_name):
        """Create a default PersistentVolume of hostPath type.
        """
        vol_conf = {
            "kind": "PersistentVolume",
            "apiVersion": "v1",
            "metadata": {"name": volume_name, "labels": {"type": "host"},},
            "spec": {
                "persistentVolumeReclaimPolicy": "Recycle",
                "storageClassName": "manual",
                "capacity": {"storage": "1Gi",},
                "accessModes": ["ReadWriteMany"],
                "hostPath": {"path": "/tmp"},
            },
        }

        self._kclient.create_persistent_volume(body=vol_conf)

        counter = 1
        while True:
            response = self._kclient.read_persistent_volume(volume_name)
            if response.status.phase != "Pending":
                break

            log.debug(f"volume {volume_name} not created yet")

            if counter == 60:
                raise Exception("Timed out waiting for PersistentVolume creation")

            time.sleep(1)
            counter += 1

    def _vol_claim_create(self):
        """Create a PersistentVolumeClaim to claim usable storage space 
        from a previously created PersistentVolume.
        """
        if self._config.resman_opts.get("persistent_volume_name", None):
            volume_name = self._config.resman_opts.persistent_volume_name
        else:
            volume_name = f"pv-hostpath-popper-{self._config.wid}"
            if not self._vol_exists(volume_name):
                self._vol_create(volume_name)

        vol_claim_conf = {
            "apiVersion": "v1",
            "kind": "PersistentVolumeClaim",
            "metadata": {"name": self._vol_claim_name},
            "spec": {
                "storageClassName": "manual",
                "accessModes": ["ReadWriteMany"],
                "resources": {"requests": {"storage": self._vol_size}},
                "volumeName": volume_name,
            },
        }

        self._kclient.create_namespaced_persistent_volume_claim(
            namespace=self._namespace, body=vol_claim_conf
        )

        # wait for the volume claim to go into `Bound` state.
        counter = 1
        while True:
            response = self._kclient.read_namespaced_persistent_volume_claim(
                self._vol_claim_name, namespace=self._namespace
            )
            if response.status.phase != "Pending":
                break

            log.debug(f"volume claim {self._vol_claim_name} not created yet")

            if counter == 60:
                raise Exception("Timed out waiting for PersistentVolumeClaim creation")

            time.sleep(1)
            counter += 1

    def _vol_exists(self, volume_name):
        vol_exists = False
        try:
            self._kclient.read_persistent_volume(volume_name)
            vol_exists = True
        except ApiException as e:
            if e.reason != "Not Found":
                raise Exception(e)

        return vol_exists

    def _vol_claim_exists(self):
        vol_claim_exists = False
        try:
            self._kclient.read_namespaced_persistent_volume_claim(
                self._vol_claim_name, namespace=self._namespace
            )
            vol_claim_exists = True
        except ApiException as e:
            if e.reason != "Not Found":
                raise Exception(e)

        return vol_claim_exists

    def _vol_claim_delete(self):
        """Delete the PersistentVolumeClaim.
        """
        log.debug(f"deleting volume claim {self._vol_claim_name}")
        self._kclient.delete_namespaced_persistent_volume_claim(
            self._vol_claim_name, namespace=self._namespace, body=V1DeleteOptions()
        )

    def _pod_create(self, step, image, pod_host_node=None):
        """Start a Pod for each step.
        """
        log.debug(f"trying to start step pod on {pod_host_node}")
        env = self._prepare_environment(step)
        log.debug(env)

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

        if len(env.keys()) > 0:
            pod_conf["spec"]["containers"][0]["env"] = []
            for name, value in env.items():
                pod_conf["spec"]["containers"][0]["env"].append(
                    {"name": name, "value": value}
                )

        if pod_host_node:
            pod_conf["spec"]["nodeSelector"] = {"kubernetes.io/hostname": pod_host_node}

        runs = list(step.runs) if step.runs else None
        args = list(step.args) if step.args else None

        if runs:
            pod_conf["spec"]["containers"][0]["command"] = runs

        if args:
            pod_conf["spec"]["containers"][0]["args"] = args

        self._kclient.create_namespaced_pod(body=pod_conf, namespace=self._namespace)

        counter = 1
        while True:
            response = self._kclient.read_namespaced_pod(
                self._pod_name, namespace=self._namespace
            )
            if response.status.phase != "Pending":
                break

            log.debug(f"pod {self._pod_name} not started yet")

            if counter == self._config.resman_opts.get("pod_retry_limit", 60):
                raise Exception("Timed out waiting for Pod to start")

            time.sleep(1)
            counter += 1

    def _pod_read_log(self):
        """Read logs from the Pod after it moves into `Running` state.
        """
        log.debug(f"reading logs from {self._pod_name}")
        response = self._kclient.read_namespaced_pod_log(
            name=self._pod_name,
            namespace=self._namespace,
            follow=True,
            tail_lines=10,
            _preload_content=False,
        )
        for line in response:
            log.step_info(line.decode().rstrip())

    def _pod_exit_code(self):
        """Read the exit code from the Pod to decide the exit code of the step.
        """
        time.sleep(2)
        response = self._kclient.read_namespaced_pod(
            name=self._pod_name, namespace=self._namespace
        )
        log.debug(f"got status {response.status.phase}")
        if response.status.phase != "Succeeded":
            return 1
        return 0

    def _pod_delete(self):
        """Delete the Pod after it has Completed or Failed.
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
