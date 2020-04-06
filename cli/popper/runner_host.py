import os
import signal

import docker

from popper import utils as pu
from popper import scm
from popper.cli import log as log
from popper.runner import StepRunner as StepRunner


class HostRunner(StepRunner):
    """Run a step directly on the host machine."""

    def __init__(self, config):
        super(HostRunner, self).__init__(config)

        self.spawned_pids = set()

        if self.config.reuse:
            log.warning('Reuse not supported for HostRunner.')

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        pass

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

        pid, ecode, _ = pu.exec_cmd(cmd, step_env, self.config.workspace_dir,
                                    self.spawned_pids)
        if pid != 0:
            self.spawned_pids.remove(pid)

        return ecode

    def stop_running_tasks(self):
        for pid in self.spawned_pids:
            log.info(f'Stopping proces {pid}')
            os.kill(pid, signal.SIGKILL)


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

        container = self._find_container(cid)
        if container and not self.config.reuse and not self.config.dry_run:
            container.remove(force=True)

        container = self._create_container(cid, step)

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

    def _create_container(self, cid, step):
        build, img, tag, dockerfile = self._get_build_info(step)

        if build:
            log.info(f'[{step["name"]}] docker build {img}:{tag}')
            if not self.config.dry_run:
                self.d.images.build(path=dockerfile, tag=f'{img}:{tag}',
                                    rm=True, pull=True)
        elif not self.config.skip_pull and not step.get('skip_pull', False):
            log.info(f'[{step["name"]}] docker pull {img}:{tag}')
            if not self.config.dry_run:
                self.d.images.pull(repository=f'{img}:{tag}')

        log.info(f'[{step["name"]}] docker create {img}:{tag}')
        if self.config.dry_run:
            return

        container_args = self._get_container_kwargs(step, f'{img}:{tag}', cid)
        container = self.d.containers.create(**container_args)

        return container

    def _get_container_kwargs(self, step, img, name):
        args = {
            "image": img,
            "command": step.get('args', None),
            "name": name,
            "volumes": [
                f'{self.config.workspace_dir}:/workspace',
                '/var/run/docker.sock:/var/run/docker.sock'
            ],
            "working_dir": '/workspace',
            "environment": StepRunner.prepare_environment(step),
            "entrypoint": step.get('runs', None),
            "detach": True
        }

        self._update_with_engine_config(args)

        log.debug(f'container args: {pu.prettystr(args)}\n')

        return args

    def _find_container(self, cid):
        """Check whether the container exists."""
        containers = self.d.containers.list(all=True, filters={'name': cid})

        filtered_containers = [c for c in containers if c.name == cid]

        if len(filtered_containers):
            return filtered_containers[0]

        return None

    def _update_with_engine_config(self, container_args):
        update_with = self.config.engine_opts
        if not update_with:
            return

        container_args["volumes"] = [*container_args["volumes"],
                                     *update_with.get('volumes', list())]
        for k, v in update_with.get('environment', dict()).items():
            container_args["environment"].update({k: v})

        for k, v in update_with.items():
            if k not in container_args.keys():
                container_args[k] = update_with[k]
