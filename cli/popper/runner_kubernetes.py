import os
import time

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

        # pod properties
        self._pod_name = pu.sanitized_name('pod', self._config.wid)
        self._pod_name = self._pod_name.replace('_', '-')

        # volume and vol claim properties
        self._vol_name = f'{self._pod_name}-pv'
        self._vol_claim_name = f'{self._pod_name}-pvc'
        self._vol_size = self._config.resman_opts.get('volume_size', '5Gi') # same for vol claim

        # keep track of volume or volume claim are created or not
        self._vol_created = False
        self._vol_claim_created = False

    def __exit__(self, exc_type, exc_value, exc_traceback):
        super(KubernetesRunner, self).__exit__(exc_type, exc_value, exc_traceback)
        return True

    def run(self, step):
        """Execute a step in a kubernetes cluster."""
        self._build_and_push_image(step)

        m = f'[{step["name"]}] kubernetes run default.{self._pod_name}'
        log.info(m)

        if self._config.dry_run:
            return 1

        ecode = 1
        try:
            if self._is_vol_claim_created():
                self._vol_delete()

            self._vol_claim_create()
            self._pod_create(step)
            self._pod_read_log()
            ecode = self._pod_exit_code()
        except Exception as e:
            log.fail(e)
        finally:
            self._pod_delete()

        log.debug(f"Returning with {ecode}")
        return ecode

    def _build_and_push_image(self, step):
        raise NotImplementedError("Needs implementation in derived class.")

    def stop_running_tasks(self):
        self._pod_delete()

    # check volume claim
    def _is_vol_claim_created(self):
        created = True
        try:
            self._kclient.read_namespaced_persistent_volume_claim_status(
                self._vol_claim_name, 'default')
        except client.rest.ApiException:
            log.debug('Volume claim not found')
            created = False
        return created

    # create the volume
    def _vol_create(self):
        if self._vol_created:
            return

        self._kclient.create_persistent_volume(body=self._vol_conf())
        self._vol_created = True

    # create the volume claim
    def _vol_claim_create(self):
        if self._vol_claim_created:
            return

        self._kclient.create_namespaced_persistent_volume_claim(
            namespace='default', body=self._vol_claim_conf())

        counter = 1
        while True:
            resp = self._kclient.read_namespaced_persistent_volume_claim(
                self._vol_claim_name, namespace='default')

            log.debug(resp.status.phase)
            if resp.status.phase != 'Pending':
                break

            log.debug(f'Volume {self._vol_claim_name} not created yet')

            if counter == 10:
                self._vol_delete()
                raise Exception('Timed out waiting for volume creation')

            time.sleep(1)
            # counter += 1

        self._vol_claim_created  = True

    # supply the volume conf
    def _vol_conf(self):
        vol_conf = {
            'apiVersion': 'v1',
            'kind': 'PersistentVolume',
            'metadata': {'name': self._vol_name},
            'spec': {
                # 'storageClassName': 'manual',
                'accessModes': ['ReadWriteOnce'],
                'hostPath': {
                    'path': os.getcwd()
                },
                'capacity': {
                    'storage': self._vol_size
                }
            }
        }
        log.debug(f'Volume spec: {vol_conf}')
        return vol_conf

    # supply the vol claim conf
    def _vol_claim_conf(self):
        vol_claim_conf = {
            'apiVersion': 'v1',
            'kind': 'PersistentVolumeClaim',
            'metadata': {
                'name': self._vol_claim_name
            },
            'spec': {
                # 'storageClassName': 'manual',
                'accessModes': ['ReadWriteMany'],
                'resources': {
                    'requests': {
                        'storage': self._vol_size
                    }
                }
            }
        }
        log.debug(f'Volume Claim spec: {vol_claim_conf}')
        return vol_claim_conf

    # wait for sometime and create pod from step
    def _pod_create(self, step):
        pod_conf = self._pod_conf(step)

        self._kclient.create_namespaced_pod(body=pod_conf,
                                           namespace='default')

        counter = 1
        while True:
            resp = self._kclient.read_namespaced_pod(self._pod_name,
                                                    namespace='default')
            log.debug(resp.status)
            if resp.status.phase != 'Pending':
                break

            log.debug(f'Pod {self._pod_name} not started yet')

            if counter == 10:
                raise Exception('Timed out waiting for pod to start')

            time.sleep(1)
            # counter += 1

    # supply pod conf
    def _pod_conf(self, step):
        ws_vol_mount = f'{self._pod_name}-ws'
        pod_conf = {
            'apiVersion': 'v1',
            'kind': 'Pod',
            'metadata': {'name': self._pod_name},
            'spec': {
                'restartPolicy': 'Never',
                'containers': [{
                    'image': f'{step["uses"].replace("docker://", "")}',
                    'name': f'{step["name"]}',
                    'command': step.get('command', []),
                    'args': step.get('args', []),
                    'workingDir': '/workspace',
                    'volumeMounts': [{
                        'name':  ws_vol_mount,
                        'mountPath': '/workspace',
                    }]
                }],
                'volumes': [{
                    'name': ws_vol_mount,
                    'persistentVolumeClaim': {'claimName': self._vol_claim_name},
                }]
            }
        }
        log.debug(f'Pod spec: {pod_conf}')

        return pod_conf

    def _pod_read_log(self):
        log.debug(f'Reading logs')
        resp = self._kclient.read_namespaced_pod_log(name=self._pod_name,
                                                    namespace='default',
                                                    follow=True,
                                                    tail_lines=10,
                                                    _preload_content=False)
        for line in resp:
            log.step_info(line.decode())

    def _pod_exit_code(self):
        resp = self._kclient.read_namespaced_pod(name=self._pod_name,
                                                namespace='default')
        log.debug(f'Got status {resp.status.phase}')
        if resp.status.phase != 'Succeeded':
            return 1
        return 0

    def _vol_delete(self):
        log.debug(f'deleting volume {self._vol_claim_name}')
        self._kclient.delete_namespaced_persistent_volume_claim(self._vol_claim_name,
                                           namespace='default',
                                           body=V1DeleteOptions())

    def _pod_delete(self):
        log.debug(f'deleting pod {self._pod_name}')
        self._kclient.delete_namespaced_pod(self._pod_name,
                                           namespace='default',
                                           body=V1DeleteOptions())


class DockerRunner(KubernetesRunner, HostDockerRunner):
    """Runs steps on kubernetes; builds images locally using docker.
    """
    def __init__(self, **kw):
        super(DockerRunner, self).__init__(**kw)

    def _build_and_push_image(self, step):
        needs_build, img, tag, build_ctx_path = self._get_build_info(step)
        if not needs_build:
            return
        if not self._config.registry:
            raise Exception("Expecting 'registry' option in configuration.")
        img = f"{self._config.registry}/{img}"
        self._d.images.build(path=build_ctx_path, tag=f'{img}:{tag}', rm=True, pull=True)

        step['uses'] = f"{img}:{tag}"
        for l in self._d.images.push(img, tag=tag, stream=True, decode=True):
            log.step_info(l)
