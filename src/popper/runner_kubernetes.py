import os
import base64
import time
import tarfile

from kubernetes import config, client
from kubernetes.client import Configuration, V1DeleteOptions
from kubernetes.client.api import core_v1_api
from kubernetes.stream import stream

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
        """Delete the Pod and then the PersistentVolumeClaim upon receiving SIGINT.
        """
        log.debug("received SIGINT. deleting pod and volume claim")
        self._pod_delete()
        self._vol_claim_delete()

    def _copy_ctx(self):
        """Tar up the workspace context and copy the tar file into
        the PersistentVolume in the Pod.
        """
        files = os.listdir(self._config.workspace_dir)
        with tarfile.open("ctx" + ".tar.gz", mode="w:gz") as archive:
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

        source_file = "ctx.tar.gz"
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

        if self._config.resman_opts.node_selector_host_name:
            init_pod_conf["spec"]["nodeSelector"] = {
                "kubernetes.io/hostname": self._config.resman_opts.node_selector_host_name
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

            if counter == self._config.resman_opts.get("step_pod_retry_limit", 60):
                raise Exception("Timed out waiting for init pod to start")

            time.sleep(1)
            counter += 1

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
            response = self._kclient.read_namespaced_pod(
                self._pod_name, namespace=self._namespace
            )
            if response.status.phase != "Pending":
                break

            log.debug(f"pod {self._pod_name} not started yet")

            if counter == self._config.resman_opts.get("step_pod_retry_limit", 60):
                raise Exception("Timed out waiting for Pod to start")

            time.sleep(1)
            counter += 1

    def _pod_read_log(self):
        """Read logs from the Pod after it moves into `Completed` state.
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
        """Clones the action repository, builds the image
        and pushes the image to an  an image registry for a Pod to use.
        """
        needs_build, img, tag, build_ctx_path = self._get_build_info(step)
        if not needs_build:
            return step.uses.replace("docker://", "")

        if not self._config.resman_opts.registry:
            raise Exception("Expecting 'registry' option in configuration.")

        if not self._config.resman_opts.registry_user:
            raise Exception("Expecting 'registry_user' option in configuration.")

        # TODO: this needs to be changed. password should not be in config
        if not self._config.resman_opts.registry_password:
            raise Exception("Expecting 'registry_password' option in configuration.")

        img = img.replace("/", "_")
        img = f"{self._config.resman_opts.registry}/{self._config.resman_opts.registry_user}/{img}"

        self._d.images.build(
            path=build_ctx_path, tag=f"{img}:{tag}", rm=True, pull=True
        )

        self._d.login(
            self._config.resman_opts.registry_user,
            self._config.resman_opts.registry_password,
        )
        log.debug("login successful")

        for l in self._d.images.push(img, tag=tag, stream=True, decode=True):
            log.step_info(l)

        log.debug(f"image built {img}:{tag}")
        return f"{img}:{tag}"
