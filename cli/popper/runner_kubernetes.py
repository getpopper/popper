import time

from kubernetes import config
from kubernetes.client import Configuration, V1DeleteOptions
from kubernetes.client.api import core_v1_api

from popper import utils as pu
from popper.cli import log as log
from popper.runner import StepRunner as StepRunner
from popper.runner_host import DockerRunner as HostDockerRunner


class KubernetesRunner(StepRunner):
    """Base class for all kubernetes step runners"""
    def __init__(self, conf):
        super(KubernetesRunner, self).__init__(conf)

        config.load_kube_config()

        c = Configuration()
        c.assert_hostname = False
        Configuration.set_default(c)
        self.kclient = core_v1_api.CoreV1Api()

        _, active_context = config.list_kube_config_contexts()
        self.namespace = active_context['name']

        self.pod_name = pu.sanitized_name('pod', self.config.wid)
        self.pod_name = self.pod_name.replace('_', '-')

        self.vol_name = f'{self.pod_name}-pv'
        self.vol_size = self.config.resman_options.get('volume_size', '10Gi')
        self.vol_created = False

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.kclient.close()
        return True

    def run(self, step):
        """Execute a step in a kubernetes cluster."""
        self._build_and_push_image(step, push=True)

        m = f'[{step["name"]}] kubernetes run {self.namespace}.{self.pod_name}'
        log.info(m)

        if self.config.dry_run:
            return 1

        ecode = 1
        try:
            self._vol_create()
            self._pod_create(step)
            self._pod_read_log()
            ecode = self._pod_exit_code()
        except Exception as e:
            log.fail(e)
        finally:
            self._pod_delete()

        return ecode

    def _build_and_push_image(self, step):
        raise NotImplementedError("Needs implementation in derived class.")

    def stop_running_tasks(self):
        self._pod_delete()

    def _vol_create(self, vol_conf):
        if self.vol_created:
            return

        vol_conf = self._vol_conf()

        self.kclient.create_namespaced_persistent_volume_claim(
            namespace=self.namespace, body=vol_conf)

        counter = 1
        while True:
            resp = self.kclient.read_namespaced_volume_claim(
                self.vol_name, namespace=self.namespace)

            if resp.status.phase != 'Pending':
                break

            log.debug(f'Volume {self.vol_name} not created yet')

            if counter == 10:
                self._delete_volume(self.vol_name)
                raise Exception('Timed out waiting for volume creation')

            time.sleep(1)

        self.vol_created = True

    def _vol_conf(self):
        vol_conf = {
            'apiVersion': 'v1',
            'kind': 'PersistentVolumeClaim',
            'metadata': {'name': self.vol_name},
            'spec': {
                'accessModes': 'ReadWrite',
                'resources': {'request': self.vol_size},
            }
        }
        log.debug(f'Volume spec: {vol_conf}')
        return vol_conf

    def _pod_create(self, step):
        pod_conf = self._pod_conf(step)

        self.kclient.create_namespaced_pod(body=pod_conf,
                                           namespace=self.namespace)

        counter = 1
        while True:
            resp = self.kclient.read_namespaced_pod(self.pod_name,
                                                    namespace=self.namespace)
            if resp.status.phase != 'Pending':
                break

            log.debug(f'Pod {self.pod_name} not started yet')

            if counter == 10:
                raise Exception('Timed out waiting for pod to start')

            time.sleep(1)

    def _pod_conf(self, step):
        ws_vol_mount = f'{self.podname}-ws'
        pod_conf = {
            'apiVersion': 'v1',
            'kind': 'Pod',
            'metadata': {'name': self.pod_name},
            'spec': {
                'restartPolicy': 'Never',
                'containers': [{
                    'image': f'{step["uses"].replace("docker://", "")}',
                    'name': f'{step["name"]}',
                    'command': step.get('command', []),
                    'args': step.get('args', []),
                    'volumeMounts': [{
                        'name':  ws_vol_mount,
                        'mountPath': '/workspace',
                    }]
                }],
                'volumes': [{
                    'name': ws_vol_mount,
                    'persistentVolumeClaim': {'claimName': self.vol_name},
                }]
            }
        }
        log.debug(f'Pod spec: {pod_conf}')

        return pod_conf

    def _pod_read_log(self):
        log.debug(f'Reading logs')
        resp = self.kclient.read_namespaced_pod_log(name=self.pod_name,
                                                    namespace=self.namespace,
                                                    follow=True,
                                                    tail_lines=10,
                                                    _preload_content=False)
        for line in resp:
            log.step_info(line)

    def _pod_exit_code(self):
        resp = self.kclient.read_namespaced_pod(name=self.pod_name,
                                                namespace=self.namespace)
        log.debug(f'Got status {resp.status.phase}')
        if resp.status.phase != 'Succeeded':
            return 1
        return 0

    def _vol_delete(self):
        log.debug(f'deleting volume {self.vol_name}')
        self.kclient.delete_namespaced_pod(self.vol_name,
                                           namespace=self.namespace,
                                           body=V1DeleteOptions())

    def _pod_delete(self):
        log.debug(f'deleting pod {self.pod_name}')
        self.kclient.delete_namespaced_pod(self.pod_name,
                                           namespace=self.namespace,
                                           body=V1DeleteOptions())


class DockerRunner(StepRunner, HostDockerRunner):
    """Runs steps on kubernetes; builds images locally using docker.
    """
    def __init__(self, conf):
        super(DockerRunner, self).__init__(conf)

    def build_and_push_image(self, step):
        needs_build, img, tag, dockerfile = self._get_build_info(step)
        if not needs_build:
            return
        if not self.config.registry:
            raise Exception("Expecting 'registry' option in configuration.")
        img = f'{self.config.registry}/{img}'
        self.d.images.build(path=path, tag=f'{img}:{tag}', rm=True, pull=True)
        for l in self.d.push(img, tag=tag, stream=True, decode=True):
            log.step_info(l)
