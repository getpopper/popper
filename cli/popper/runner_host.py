import os

from subprocess import PIPE, Popen, STDOUT, SubprocessError

import docker

from popper import utils as pu
from popper import scm
from popper.cli import log as log
from popper.runner import StepRunner as StepRunner


class HostRunner(StepRunner):
    """Run an step on the Host Machine."""

    spawned_processes = set()

    def __init__(self, config):
        super(HostRunner, self).__init__(config)
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

        ecode = pu.exec_cmd(
            cmd,
            step_env,
            self.config.workspace_dir,
            HostRunner.spawned_processes)
        return ecode

    def stop_running_tasks(self):
        for p in HostRunner.spawned_processes:
            log.info(f'Stopping proces {p.pid}')
            p.kill()


class DockerRunner(StepRunner):
    """Runs steps in docker."""
    d = None

    # hold references to spawned containers
    spawned_containers = []

    def __init__(self, config):
        super(DockerRunner, self).__init__(config)

        try:
            DockerRunner.d = docker.from_env()
            DockerRunner.d.version()
        except Exception as e:
            log.debug(f'Docker error: {e}')
            log.fail(f'Unable to connect to the docker daemon.')

        log.debug(f'Docker info: {pu.prettystr(DockerRunner.d.info())}')

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if DockerRunner.d:
            DockerRunner.d.close()
        DockerRunner.spawned_containers = []
        return True

    def run(self, step):
        """Execute the given step in docker."""
        cid = pu.sanitized_name(step['name'], self.config.wid)

        container = DockerRunner.find_container(cid)

        if container and not self.config.reuse and not self.config.dry_run:
            container.remove(force=True)

        container = DockerRunner.create_container(cid, step, self.config)

        log.info(f'[{step["name"]}] docker start')

        if self.config.dry_run:
            return 0

        DockerRunner.spawned_containers.append(container)

        container.start()
        cout = container.logs(stream=True)
        for line in cout:
            log.step_info(pu.decode(line).strip('\n'))

        e = container.wait()['StatusCode']
        return e

    def stop_running_tasks(self):
        for c in DockerRunner.spawned_containers:
            log.info(f'Stopping container {c.name}')
            c.stop()

    @staticmethod
    def prepare_image(step, config):
        build, img, dockerfile = DockerRunner.get_build_info(
            step, config.workspace_dir, config.workspace_sha)

        if build:
            DockerRunner.docker_build(step, img, dockerfile,
                                      config.dry_run)
        elif not config.skip_pull and not step.get('skip_pull', False):
            DockerRunner.docker_pull(step, img, config.dry_run)

        return build, img, dockerfile

    @staticmethod
    def get_engine_config(step, img, cid, config):
        engine_config = {
            "image": img,
            "command": step.get('args', []),
            "name": cid,
            "volumes": [
                f'{config.workspace_dir}:/workspace',
                '/var/run/docker.sock:/var/run/docker.sock'
            ],
            "working_dir": '/workspace',
            "environment": StepRunner.prepare_environment(step),
            "entrypoint": step.get('runs', []),
            "detach": True
        }
        return engine_config

    @staticmethod
    def create_container(cid, step, config):
        build, img, dockerfile = DockerRunner.prepare_image(step, config)
        msg = f'{img} {step.get("runs", "")} {step.get("args", "")}'
        log.info(f'[{step["name"]}] docker create {msg}')

        if config.dry_run:
            return

        engine_config = DockerRunner.get_engine_config(step, img, cid, config)

        if config.engine_options:
            DockerRunner.update_engine_config(
                engine_config, config.engine_options)
        log.debug(f'Engine configuration: {pu.prettystr(engine_config)}\n')

        container = DockerRunner.d.containers.create(**engine_config)
        return container

    @staticmethod
    def get_build_info(step, workspace_dir, workspace_sha):
        """Parses the `uses` attribute and returns build information needed.

        Args:
            step(dict): dict with step data

        Returns:
            (str, str, str): 'pull' or 'build', image ref, path to Dockerfile
        """
        build = True
        img = None
        build_source = None

        if 'docker://' in step['uses']:
            img = step['uses'].replace('docker://', '')
            if ':' not in img:
                img += ":latest"
            build = False
        elif './' in step['uses']:
            img = f'{pu.sanitized_name(step["name"], "step")}:{workspace_sha}'
            build_source = os.path.join(workspace_dir, step['uses'])
        else:
            _, _, user, repo, _, version = scm.parse(step['uses'])
            img = f'{user}/{repo}:{version}'
            build_source = os.path.join(step['repo_dir'], step['step_dir'])

        return (build, img.lower(), build_source)

    @staticmethod
    def find_container(cid):
        """Check whether the container exists."""
        containers = DockerRunner.d.containers.list(
            all=True, filters={'name': cid})

        filtered_containers = [c for c in containers if c.name == cid]

        if len(filtered_containers):
            return filtered_containers[0]

        return None

    @staticmethod
    def docker_image_exists(img):
        """Check whether a docker image exists for a step not.

        Args:
          img(str): The image to check for.

        Returns:
          bool: Whether the image exists or not.
        """
        images = DockerRunner.d.images.list(all=True)
        filtered_images = [i for i in images if img in i.tags]
        if filtered_images:
            return True
        return False

    @staticmethod
    def update_engine_config(engine_conf, update_with):
        engine_conf["volumes"] = [*engine_conf["volumes"],
                                  *update_with.get('volumes', list())]
        for k, v in update_with.get('environment', dict()).items():
            engine_conf["environment"].update({k: v})

        for k, v in update_with.items():
            if k not in engine_conf.keys():
                engine_conf[k] = update_with[k]

    @staticmethod
    def docker_pull(step, img, dry_run):
        """Pull an image from a container registry.

        Args:
          img(str): The image reference to pull.

        Returns:
            None
        """
        log.info(f'[{step["name"]}] docker pull {img}')
        if dry_run:
            return
        DockerRunner.d.images.pull(repository=img)

    @staticmethod
    def docker_build(step, tag, path, dry_run):
        """Build a docker image from a Dockerfile.

        Args:
          tag(str): The name of the image to build.
          path(str): The path to the Dockerfile.

        Returns:
            None
        """
        log.info(f'[{step["name"]}] docker build -t {tag} {path}')
        if dry_run:
            return
        DockerRunner.d.images.build(path=path, tag=tag, rm=True, pull=True)
