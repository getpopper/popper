import time

from kubernetes import config
from kubernetes.client import Configuration, V1DeleteOptions
from kubernetes.client.api import core_v1_api

from popper import utils as pu
from popper.cli import log as log
from popper.runner import StepRunner as StepRunner


class DockerRunner(StepRunner):
    """Run a step on kubernetes; builds images locally using docker.
    """
    def __init__(self, conf):
        super(DockerRunner, self).__init__(conf)

        config.load_kube_config()

        c = Configuration()
        c.assert_hostname = False
        Configuration.set_default(c)
        self.kclient = core_v1_api.CoreV1Api()

        _, active_context = config.list_kube_config_contexts()
        self.namespace = active_context['name']

        self.pod_name = pu.sanitized_name('pod', self.config.wid)
        self.pod_name = self.pod_name.replace('_', '-')

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.kclient.close()
        return True

    def run(self, step):
        """Execute the given step in kubernetes."""
        if not step["uses"].startswith('docker://'):
            raise ValueError("Kubernetes runner cannot build images yet")

        pod = self.__pod_spec(step)

        log.info(f'[{step["name"]}] kubernetes run pod {pod["spec"]}')

        if self.config.dry_run:
            return 1

        ecode = 1
        try:
            # self.__create_remote_workspace()
            self.__pod_create(pod)
            self.__pod_read_log()
            ecode = self.__pod_exit_code()
        except Exception as e:
            log.fail(e)
        finally:
            self.__pod_delete()

        return ecode

    def stop_running_tasks(self):
        self.__pod_delete()

    def __pod_spec(self, step):
        pod = {
            'apiVersion': 'v1',
            'kind': 'Pod',
            'metadata': {'name': self.pod_name},
            'spec': {
                'restartPolicy': 'Never',
                'containers': [{
                    'image': f'{step["uses"].replace("docker://", "")}',
                    'name': f'{step["name"]}',
                    'command': step.get('command', []),
                    'args': step.get('args', [])
                }]
            }
        }
        log.debug(f'Using namespace: {self.namespace}')
        log.debug(f'Pod spec: {pod}')

        return pod

    def __pod_create(self, pod):
        self.kclient.create_namespaced_pod(body=pod, namespace=self.namespace)

        counter = 1
        while True:
            resp = self.kclient.read_namespaced_pod(self.pod_name,
                                                    namespace=self.namespace)
            if resp.status.phase != 'Pending':
                break

            log.debug(f'Pod {self.pod_name} not started yet')

            if counter == 10:
                self.__delete_pod(pod)
                raise Exception('Timed out waiting for pod to start')

            time.sleep(1)

    def __pod_read_log(self):
        log.debug(f'Reading logs')
        resp = self.kclient.read_namespaced_pod_log(name=self.pod_name,
                                                    namespace=self.namespace,
                                                    follow=True,
                                                    tail_lines=10,
                                                    _preload_content=False)
        for line in resp:
            log.step_info(line)

    def __pod_exit_code(self):
        resp = self.kclient.read_namespaced_pod(name=self.pod_name,
                                                namespace=self.namespace)
        log.debug(f'Got status {resp.status.phase}')
        if resp.status.phase != 'Succeeded':
            return 1
        return 0

    def __pod_delete(self):
        log.debug(f'deleting pod {self.pod_name}')
        self.kclient.delete_namespaced_pod(self.pod_name,
                                           namespace=self.namespace,
                                           body=V1DeleteOptions())
