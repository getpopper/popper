import os
import signal
import threading

import docker

from subprocess import Popen, STDOUT, PIPE, SubprocessError, CalledProcessError

import spython
from spython.main.parse.parsers import DockerParser
from spython.main.parse.writers import SingularityWriter

from popper import utils as pu
from popper import scm
from popper.cli import log as log
from popper.runner import StepRunner as StepRunner, WorkflowRunner


class HostRunner(StepRunner):
    """Run a step directly on the host machine."""

    def __init__(self, **kw):
        super(HostRunner, self).__init__(**kw)

        self._spawned_pids = set()

        if self._config.reuse:
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

        if self._config.dry_run:
            return 0

        log.debug(f'Environment:\n{pu.prettystr(os.environ)}')

        pid, ecode, _ = HostRunner._exec_cmd(cmd, step_env,
                                             self._config.workspace_dir,
                                             self._spawned_pids)
        if pid != 0:
            self._spawned_pids.remove(pid)

        return ecode

    def stop_running_tasks(self):
        for pid in self._spawned_pids:
            log.info(f'Stopping proces {pid}')
            os.kill(pid, signal.SIGKILL)

    @staticmethod
    def _exec_cmd(cmd, env=None, cwd=os.getcwd(), pids=set(), logging=True):
        pid = 0
        try:
            with Popen(cmd, stdout=PIPE, stderr=STDOUT,
                       universal_newlines=True, preexec_fn=os.setsid,
                       env=env, cwd=cwd) as p:
                pid = p.pid
                pids.add(p.pid)
                log.debug('Reading process output')

                output = []
                for line in iter(p.stdout.readline, ''):
                    if logging:
                        log.step_info(line)
                    else:
                        output.append(line)

                p.wait()
                ecode = p.poll()

            log.debug(f'Code returned by process: {ecode}')

        except SubprocessError as ex:
            output = ""
            ecode = ex.returncode
            log.step_info(f"Command '{cmd[0]}' failed with: {ex}")
        except Exception as ex:
            output = ""
            ecode = 1
            log.step_info(f"Command raised non-SubprocessError error: {ex}")

        return pid, ecode, '\n'.join(output)


class DockerRunner(StepRunner):
    """Runs steps in docker on the local machine."""

    def __init__(self, init_docker_client=True, **kw):
        super(DockerRunner, self).__init__(**kw)

        self._spawned_containers = set()
        self._d = None

        if not init_docker_client:
            return

        try:
            self._d = docker.from_env()
            self._d.version()
        except Exception as e:
            log.debug(f'Docker error: {e}')
            log.fail(f'Unable to connect to the docker daemon.')

        log.debug(f'Docker info: {pu.prettystr(self._d.info())}')

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if self._d:
            self._d.close()

    def run(self, step):
        """Execute the given step in docker."""
        cid = pu.sanitized_name(step['name'], self._config.wid)

        container = self._find_container(cid)
        if container and not self._config.reuse and not self._config.dry_run:
            container.remove(force=True)

        container = self._create_container(cid, step)

        log.info(f'[{step["name"]}] docker start')

        if self._config.dry_run:
            return 0

        self._spawned_containers.add(container)

        container.start()
        cout = container.logs(stream=True)
        for line in cout:
            log.step_info(line.decode().rstrip())

        e = container.wait()['StatusCode']
        return e

    def stop_running_tasks(self):
        for c in self._spawned_containers:
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
        build_context = None

        if 'docker://' in step['uses']:
            img = step['uses'].replace('docker://', '')
            if ':' in img:
                (img, tag) = img.split(':')
            else:
                tag = 'latest'
            build = False
        elif './' in step['uses']:
            img = f'{pu.sanitized_name(step["name"], "step")}'
            tag = f'{self._config.workspace_sha}'
            build_context = os.path.join(self._config.workspace_dir,
                                        step['uses'])
        else:
            _, _, user, repo, _, version = scm.parse(step['uses'])
            img = f'{user}/{repo}'.lower()
            tag = version
            build_context = os.path.join(step['repo_dir'], step['step_dir'])

        return (build, img, tag, build_context)

    def _create_container(self, cid, step):
        build, img, tag, build_context = self._get_build_info(step)

        if build:
            log.info(
                f'[{step["name"]}] docker build {img}:{tag} {build_context}')
            if not self._config.dry_run:
                self._d.images.build(path=build_context, tag=f'{img}:{tag}',
                                     rm=True, pull=True)
        elif not self._config.skip_pull and not step.get('skip_pull', False):
            log.info(f'[{step["name"]}] docker pull {img}:{tag}')
            if not self._config.dry_run:
                self._d.images.pull(repository=f'{img}:{tag}')

        if self._config.dry_run:
            return

        container_args = self._get_container_kwargs(step, f'{img}:{tag}', cid)

        msg = f'[{step["name"]}] docker create name={cid}'
        msg += f' image={container_args["image"]}'
        if container_args["entrypoint"]:
            msg += f' entrypoint={container_args["entrypoint"]}'
        if container_args["command"]:
            msg += f' command={container_args["command"]}'
        log.info(msg)

        container = self._d.containers.create(**container_args)

        return container

    def _get_container_kwargs(self, step, img, name):
        args = {
            "image": img,
            "command": step.get('args', None),
            "name": name,
            "volumes": [
                f'{self._config.workspace_dir}:/workspace',
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
        containers = self._d.containers.list(all=True, filters={'name': cid})

        filtered_containers = [c for c in containers if c.name == cid]

        if len(filtered_containers):
            return filtered_containers[0]

        return None

    def _update_with_engine_config(self, container_args):
        """Given container arguments, it extends it so it includes options
        obtained from the PopperConfig.engine_opts property.
        """
        update_with = self._config.engine_opts
        if not update_with:
            return

        container_args["volumes"] = [*container_args["volumes"],
                                     *update_with.get('volumes', list())]
        for k, v in update_with.get('environment', dict()).items():
            container_args["environment"].update({k: v})

        for k, v in update_with.items():
            if k not in container_args.keys():
                container_args[k] = update_with[k]


class SingularityRunner(StepRunner):
    """Runs steps in singularity on the local machine."""
    lock = threading.Lock()

    def __init__(self, **kw):
        super(SingularityRunner, self).__init__(**kw)

        self._spawned_containers = set()
        self._s = None

        if self._config.reuse:
            log.fail('Reuse not supported for SingularityRunner.')

        self._s = spython.main.Client
        self._s.quiet = True

    def run(self, step):
        self._setup_singularity_cache()
        cid = pu.sanitized_name(step['name'], self._config.wid) + '.sif'
        self._container = os.path.join(self._singularity_cache, cid)

        exists = os.path.exists(self._container)
        if exists and not self._config.dry_run and not self._config.skip_pull:
            os.remove(self._container)

        self._create_container(step, cid)
        ecode = self._singularity_start(step, cid)
        return ecode

    def _convert(self, dockerfile, singularityfile):
        parser = DockerParser(dockerfile)
        for p in parser.recipe.files:
            p[0] = p[0].strip('\"')
            p[1] = p[1].strip('\"')
            if os.path.isdir(p[0]):
                p[0] += '/.'

        writer = SingularityWriter(parser.recipe)
        recipe = writer.convert()
        with open(singularityfile, 'w') as sf:
            sf.write(recipe)
        return singularityfile

    def _get_recipe_file(self, build_context, cid):
        dockerfile = os.path.join(build_context, 'Dockerfile')
        singularityfile = os.path.join(
            build_context, 'Singularity.{}'.format(cid[:-4]))

        if os.path.isfile(dockerfile):
            return self._convert(dockerfile, singularityfile)
        else:
            log.fail('No Dockerfile was found.')

    def _build_from_recipe(self, build_context, build_dest, cid):
        SingularityRunner.lock.acquire()
        pwd = os.getcwd()
        os.chdir(build_context)
        recipefile = self._get_recipe_file(build_context, cid)
        self._s.build(
            recipe=recipefile,
            image=cid,
            build_folder=build_dest)
        os.chdir(pwd)
        SingularityRunner.lock.release()

    def _get_build_info(self, step):
        build = True
        img = None
        build_context = None

        if 'docker://' in step['uses'] or 'shub://' in step['uses']:
            img = step['uses']
            build = False

        elif './' in step['uses']:
            img = f'{pu.sanitized_name(step["name"], "step")}'
            build_context = os.path.join(self._config.workspace_dir,
                                        step['uses'])
        else:
            _, _, user, repo, _, version = scm.parse(step['uses'])
            img = f'{user}/{repo}'.lower()
            build_context = os.path.join(step['repo_dir'], step['step_dir'])

        return (build, img, build_context)

    def _setup_singularity_cache(self):
        self._singularity_cache = os.path.join(
            WorkflowRunner._setup_base_cache(), 'singularity', self._config.wid)
        if not os.path.exists(self._singularity_cache):
            os.makedirs(self._singularity_cache, exist_ok=True)

    def _update_with_engine_config(self, container_args):
        update_with = self._config.engine_opts
        if not update_with:
            return

        container_args["bind"] = [*container_args["bind"],
                                  *update_with.get('bind', list())]

        for k, v in update_with.items():
            if k not in container_args.keys():
                container_args[k] = update_with[k]

    def _get_container_options(self):
        container_args = {
            'userns': True,
            'pwd': '/workspace',
            'bind': [f'{self._config.workspace_dir}:/workspace']
        }

        self._update_with_engine_config(container_args)

        options = []
        for k, v in container_args.items():
            if isinstance(v, list):
                for item in v:
                    options.append(pu.key_value_to_flag(k, item))
            else:
                options.append(pu.key_value_to_flag(k, v))

        options = ' '.join(options).split(' ')
        log.debug(f'container options: {options}\n')

        return options

    def _create_container(self, step, cid):
        build, image, build_context = self._get_build_info(step)

        if build:
            log.info(
                f'[{step["name"]}] singularity build {cid} {build_context}')
            if not self._config.dry_run:
                self._build_from_recipe(
                    build_context, self._singularity_cache, cid)
        elif not self._config.skip_pull and not step.get('skip_pull', False):
            log.info(f'[{step["name"]}] singularity pull {cid} {image}')
            if not self._config.dry_run:
                self._s.pull(
                    image=image,
                    name=cid,
                    pull_folder=self._singularity_cache)

    def _singularity_start(self, step, cid):
        env = StepRunner.prepare_environment(step)

        # set the environment variables
        for k, v in env.items():
            os.environ[k] = v

        args = step.get('args', None)
        runs = step.get('runs', None)
        ecode = None

        if runs:
            info = f'[{step["name"]}] singularity exec {cid} {runs}'
            commands = runs
            start_fn = self._s.execute
        else:
            info = f'[{step["name"]}] singularity run {cid} {args}'
            commands = args
            start_fn = self._s.run

        log.info(info)

        if self._config.dry_run:
            return 0

        options = self._get_container_options()
        output = start_fn(self._container, commands,
                       stream=True, options=options)
        try:
            for line in output:
                log.step_info(line.strip('\n'))
            ecode = 0
        except CalledProcessError as ex:
            ecode = ex.returncode

        return ecode

    def stop_running_tasks(self):
        pass
