import os
import copy
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

        # load the k8s config from host
        config.load_kube_config()

        c = Configuration()
        c.assert_hostname = False
        Configuration.set_default(c)
        self._kclient = core_v1_api.CoreV1Api()

        _, active_context = config.list_kube_config_contexts()

        self._pod_name = pu.sanitized_name(f'pod', self._config.wid)
        self._pod_name = self._pod_name.replace('_', '-')

        self._init_pod_name = pu.sanitized_name('init-pod', self._config.wid)
        self._init_pod_name = self._init_pod_name.replace('_', '-')

        self._vol_claim_name = f'{self._pod_name}-pvc'
        self._vol_size = self._config.resman_opts.get('volume_size', '500Mi')

        self._vol_claim_created = False

    def __exit__(self, exc_type, exc_value, exc_traceback):
        super(KubernetesRunner, self).__exit__(exc_type, exc_value, exc_traceback)
        return True

    def run(self, step):
        """Execute a step in a kubernetes cluster."""
        self._build_and_push_image(step)

        m = f'[{step.id}] kubernetes run default.{self._pod_name}'
        log.info(m)

        if self._config.dry_run:
            return 1

        ecode = 1
        try:
            self._vol_claim_create()
            self._init_pod_create()
            self._copy_ctx()
            self._init_pod_delete()
            self._pod_create(step)
            ecode = self._pod_exec(step)
        except Exception as e:
            log.fail(e)
        finally:
            self._pod_delete()
            self._vol_claim_delete()

        log.debug(f"Returning with {ecode}")
        return ecode


    def _build_and_push_image(self, step):
        raise NotImplementedError("Needs implementation in derived class.")


    def stop_running_tasks(self):
        self._pod_delete()


    def _init_pod_create(self):
        _ws_vol_mount = f'{self._init_pod_name}-ws'
        _init_pod_conf = {
            'apiVersion': 'v1',
            'kind': 'Pod',
            'metadata': {'name': self._init_pod_name},
            'spec': {
                'restartPolicy': 'Never',
                'containers': [{
                    'image': 'alpine:3.11',
                    'name': self._init_pod_name,
                    'workingDir': '/workspace',
                    'command': ['sleep', 'infinity'],
                    'volumeMounts': [{
                        'name':  _ws_vol_mount,
                        'mountPath': '/workspace',
                    }]
                }],
                'volumes': [{
                    'name': _ws_vol_mount,
                    'persistentVolumeClaim': {
                        'claimName': self._vol_claim_name,
                    }
                }]
            }
        }
        self._kclient.create_namespaced_pod(body=_init_pod_conf, namespace='default')

        counter = 1
        while True:
            resp = self._kclient.read_namespaced_pod(self._init_pod_name,
                                                    namespace='default')
            log.debug(resp.status)
            if resp.status.phase != 'Pending':
                break

            log.debug(f'Pod {self._init_pod_name} not started yet')

            if counter == 10:
                raise Exception('Timed out waiting for pod to start')

            time.sleep(1)
            counter += 1


    def _copy_ctx(self):
        files = os.listdir(self._config.workspace_dir)
        with tarfile.open('ctx' + '.tar.gz', mode='w:gz') as archive:
            for f in files:
                archive.add(f)

        os.system(f"kubectl cp ctx.tar.gz default/{self._init_pod_name}:/workspace")
        os.system(f"kubectl exec {self._init_pod_name} -- tar -xvf /workspace/ctx.tar.gz")


    def _init_pod_delete(self):
        log.debug(f'deleting pod {self._pod_name}')
        self._kclient.delete_namespaced_pod(self._init_pod_name,
                                           namespace='default',
                                           body=V1DeleteOptions())


    def _vol_claim_create(self):
        _vol_claim_conf = {
            'apiVersion': 'v1',
            'kind': 'PersistentVolumeClaim',
            'metadata': {
                'name': self._vol_claim_name
            },
            'spec': {
                'storageClassName': 'manual',
                'accessModes': ['ReadWriteMany'],
                'resources': {
                    'requests': {
                        'storage': self._vol_size
                    }
                }
            }
        }

        if self._vol_claim_created:
            return

        self._kclient.create_namespaced_persistent_volume_claim(
            namespace='default', body=_vol_claim_conf)

        counter = 1
        while True:
            resp = self._kclient.read_namespaced_persistent_volume_claim(
                self._vol_claim_name, namespace='default')

            log.debug(resp.status.phase)
            if resp.status.phase != 'Pending':
                break

            log.debug(f'Volume claim {self._vol_claim_name} not created yet')

            if counter == 60:
                raise Exception('Timed out waiting for volume creation')

            time.sleep(1)
            counter += 1

        self._vol_claim_created  = True

    # wait for sometime and create pod from step
    def _pod_create(self, step):
        _pod_conf = self._pod_conf(step)

        self._kclient.create_namespaced_pod(body=_pod_conf,
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
            counter += 1

    # supply pod conf
    def _pod_conf(self, step):
        _ws_vol_mount = f'{self._pod_name}-ws'
        _pod_conf = {
            'apiVersion': 'v1',
            'kind': 'Pod',
            'metadata': {'name': self._pod_name},
            'spec': {
                'restartPolicy': 'Never',
                'containers': [{
                    'image': f'{step["uses"].replace("docker://", "")}',
                    'name': f'{step.id}',
                    'workingDir': '/workspace',
                    'command': ['sleep', 'infinity'],
                    'volumeMounts': [{
                        'name':  _ws_vol_mount,
                        'mountPath': '/workspace',
                    }]
                }],
                'volumes': [{
                    'name': _ws_vol_mount,
                    'persistentVolumeClaim': {
                        'claimName': self._vol_claim_name,
                    }
                }]
            }
        }
        log.debug(f'Pod spec: {_pod_conf}')
        return _pod_conf

    def _vol_claim_delete(self):
        log.debug(f'deleting volume {self._vol_claim_name}')
        self._kclient.delete_namespaced_persistent_volume_claim(self._vol_claim_name,
                                           namespace='default',
                                           body=V1DeleteOptions())

    def _pod_exec(self, step):
        runs = step.runs if step.runs else None
        args = step.args if step.args else None

        commands = ""
        if runs:
            commands += ' '.join(list(runs)) + " "
        if args:
            commands += ' '.join(list(args)) + " "
        
        print("executing command ")
        return os.system(f"kubectl exec {self._pod_name} -- {commands}")

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
        # if not self._config.registry:
        #     raise Exception("Expecting 'registry' option in configuration.")
        # img = f"{self._config.registry}/{img}"
        img = f"docker.io/{img}"
        self._d.images.build(path=build_ctx_path, tag=f'{img}:{tag}', rm=True, pull=True)

        step['uses'] = f"{img}:{tag}"
        for l in self._d.images.push(img, tag=tag, stream=True, decode=True):
            log.step_info(l)
