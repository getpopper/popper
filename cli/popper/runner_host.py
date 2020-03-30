import os

from subprocess import PIPE, Popen, STDOUT, SubprocessError

import docker

from popper import utils as pu
from popper import scm
from popper.cli import log as log
from popper.runner import StepRunner as StepRunner


class HostRunner(StepRunner):
    """Run a step directly on the host machine."""

    def __init__(self, config):
        super(HostRunner, self).__init__(config)

        self.spawned_processes = []

        if self.config.reuse:
            log.warning('Reuse not supported for HostRunner.')

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        HostRunner.spawned_processes = set()

    def run(self, step):
        step_env = StepRunner.prepare_environment(step, os.environ)

        cmd = step.get('runs', [])
        if not cmd:
            raise AttributeError(f"Expecting 'runs' attribute in step.")
        cmd.extend(step.get('args', []))

        log.info(f'[{step["name"]}] {cmd}')

        if self.config.dry_run:
            return 0

        log.debug(f'Environment:\n{pu.prettystr(os.environ)}')

        ecode, _ = pu.exec_cmd(
            cmd,
            step_env,
            self.config.workspace_dir,
            HostRunner.spawned_processes)
        return ecode

    def stop_running_tasks(self):
        for p in self.spawned_processes:
            log.info(f'Stopping proces {p.pid}')
            p.kill()


class DockerRunner(StepRunner):
    """Runs steps in docker on the local machine."""
    # hold references to spawned containers
    def __init__(self, config):
        super(DockerRunner, self).__init__(config)

        self.spawned_containers = []

        try:
            self.d = docker.from_env()
            self.d.version()
        except Exception as e:
            log.debug(f'Docker error: {e}')
            log.fail(f'Unable to connect to the docker daemon.')

        log.debug(f'Docker info: {pu.prettystr(self.d.info())}')

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if self.d:
            self.d.close()
        self.spawned_containers = []
        return True

    def run(self, step):
        """Execute the given step in docker."""
        cid = pu.sanitized_name(step['name'], self.config.wid)

        build, img, tag, dockerfile = self._get_build_info(step)

        container = self._find_container(cid)

        if container and not self.config.reuse and not self.config.dry_run:
            container.remove(force=True)

        container = DockerRunner.create_container(cid, step, self.config)

        log.info(f'[{step["name"]}] docker start')

        if self.config.dry_run:
            return 0

        self.spawned_containers.append(container)

        container.start()
        cout = container.logs(stream=True)
        for line in cout:
            log.step_info(pu.decode(line).strip('\n'))

        e = container.wait()['StatusCode']
        return e

    def stop_running_tasks(self):
        for c in self.spawned_containers:
            log.info(f'Stopping container {c.name}')
            c.stop()

    def _pull(self, step, img, tag):
        """Pull an image from a container registry.

        Args:
          img(str): The image reference to pull.

        Returns:
            None
        """
        log.info(f'[{step["name"]}] docker pull {img}:{tag}')
        if self.config.dry_run:
            return
        self.d.images.pull(repository=f'{img}:{tag}')

    def _build(self, step, img, tag, path):
        """Build a docker image from a Dockerfile.

        Args:
          tag(str): The name of the image to build.
          path(str): The path to the Dockerfile.

        Returns:
            None
        """
        log.info(f'[{step["name"]}] docker build -t {img}:{tag} {path}')
        if self.config.dry_run:
            return
        self.d.images.build(path=path, tag=f'{img}:{tag}', rm=True, pull=True)

    def _get_build_info(self, step):
        """Parses the `uses` attribute and returns build information needed.

        Args:
            step(dict): dict with step data

        Returns:
            (str, str, str, str): bool (build), image, tag, Dockerfile
        """
        build = True
        img = None
        build_source = None

        if 'docker://' in step['uses']:
            img = step['uses'].replace('docker://', '')
            if ':' in img:
                (img, tag) = img.split(':')
            else:
                tag = 'latest'
            build = False
        elif './' in step['uses']:
            img = f'{pu.sanitized_name(step["name"], "step")}'
            tag = f'{self.config.workspace_sha}'
            build_source = os.path.join(self.config.workspace_dir,
                                        step['uses'])
        else:
            _, _, user, repo, _, version = scm.parse(step['uses'])
            img = f'{user}/{repo}'
            tag = version
            build_source = os.path.join(step['repo_dir'], step['step_dir'])

        return (build, img, tag, build_source)

    def _find_container(self, cid):
        """Check whether the container exists."""
        containers = self.d.containers.list(all=True, filters={'name': cid})

        filtered_containers = [c for c in containers if c.name == cid]

        if len(filtered_containers):
            return filtered_containers[0]

        return None

    def _update_engine_config(self, engine_conf):
        update_with = self.config.engine_options
        engine_conf["volumes"] = [*engine_conf["volumes"],
                                  *update_with.get('volumes', list())]
        for k, v in update_with.get('environment', dict()).items():
            engine_conf["environment"].update({k: v})

        for k, v in update_with.items():
            if k not in engine_conf.keys():
                engine_conf[k] = update_with[k]
