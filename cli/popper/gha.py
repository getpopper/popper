from __future__ import unicode_literals
import os
import signal
import getpass
import subprocess
import multiprocessing as mp
from copy import deepcopy
from builtins import dict
from distutils.dir_util import copy_tree
from distutils.spawn import find_executable
from concurrent.futures import ProcessPoolExecutor, as_completed
from subprocess import CalledProcessError, PIPE, Popen, STDOUT

import yaml
import docker
import spython
from spython.main.parse.parsers import DockerParser
from spython.main.parse.writers import SingularityWriter

import popper.cli
from popper.cli import log
from popper import scm, utils as pu
from popper.parser import Workflow


yaml.Dumper.ignore_aliases = lambda *args: True
docker_client = docker.from_env()
s_client = spython.main.Client


class WorkflowRunner(object):
    """A GHA workflow runner.
    """

    def __init__(self, workflow):
        self.wf = workflow
        self.wf.parse()
        self.wid = pu.get_id(os.getuid(), self.wf.workflow_path)
        log.debug('workflow:\n{}'.format(
            yaml.dump(self.wf, default_flow_style=False, default_style='')))

    @staticmethod
    def check_secrets(wf, dry_run, skip_secrets_prompt):
        """Checks whether the secrets defined in the action block is
        set in the execution environment or not.

        Note:
            When the environment variable `CI` is set to `true`,
            then the execution fails if secrets are not defined
            else it prompts the user to enter the environment vars
            during the time of execution itself.
        """
        if dry_run or skip_secrets_prompt:
            return
        for _, a in wf.action.items():
            for s in a.get('secrets', []):
                if s not in os.environ:
                    if os.environ.get('CI') == 'true':
                        log.fail('Secret {} not defined'.format(s))
                    else:
                        val = getpass.getpass(
                            'Enter the value for {} : '.format(s))
                        os.environ[s] = val

    @staticmethod
    def download_actions(wf, dry_run, skip_clone, wid):
        """Clone actions that reference a repository."""
        actions_cache = os.path.join(
            pu.setup_base_cache(), 'actions', wid
        )

        cloned = set()
        infoed = False

        for _, a in wf.action.items():
            if ('docker://' in a['uses']
                    or './' in a['uses'] or a['uses'] == 'sh'):
                continue

            url, service, user, repo, action_dir, version = scm.parse(
                a['uses'])

            repo_dir = os.path.join(
                actions_cache, service, user, repo
            )

            a['repo_dir'] = repo_dir
            a['action_dir'] = action_dir

            if dry_run:
                continue

            if skip_clone:
                if not os.path.exists(repo_dir):
                    log.fail(
                        'The required action folder \'{}\' was not '
                        'found locally.'.format(repo_dir))
                continue

            if not infoed:
                log.info('[popper] Cloning action repositories')
                infoed = True

            if '{}/{}'.format(user, repo) in cloned:
                continue

            log.info('[popper] - {}/{}/{}@{}'.format(url, user, repo, version))
            scm.clone(url, user, repo, repo_dir, version)
            cloned.add('{}/{}'.format(user, repo))

    @staticmethod
    def instantiate_runners(runtime, wf, workspace, dry_run, skip_pull, wid):
        """Factory of ActionRunner instances, one for each action.

        Note:
            If the `uses` attribute startswith a './' and does not have
            a `Dockerfile` in the referenced directory, we assume that
            it is meant to be run on the Host machine and ignore the
            runtime argument.
            Same is the case when the `uses` attribute is equal to 'sh'.
        """
        env = WorkflowRunner.get_workflow_env(wf, workspace)
        for _, a in wf.action.items():

            if a['uses'] == 'sh':
                a['runner'] = HostRunner(
                    a, workspace, env, dry_run, skip_pull, wid)
                continue

            if a['uses'].startswith('./'):
                if not os.path.isfile(
                    os.path.join(scm.get_git_root_folder(), a['uses'],
                                 'Dockerfile')):

                    a['runner'] = HostRunner(
                        a, workspace, env, dry_run, skip_pull, wid)
                    continue

            if runtime == 'docker':
                a['runner'] = DockerRunner(
                    a, workspace, env, dry_run, skip_pull, wid)

            elif runtime == 'singularity':
                a['runner'] = SingularityRunner(
                    a, workspace, env, dry_run, skip_pull, wid)

    @staticmethod
    def get_workflow_env(wf, workspace):
        if scm.get_user():
            repo_id = '{}/{}'.format(scm.get_user(), scm.get_name())
        else:
            repo_id = 'unknown'

        env = {
            'HOME': os.environ['HOME'],
            'GITHUB_WORKFLOW': wf.name,
            'GITHUB_ACTION': '',
            'GITHUB_ACTOR': 'popper',
            'GITHUB_REPOSITORY': repo_id,
            'GITHUB_EVENT_NAME': wf.on,
            'GITHUB_EVENT_PATH': '/tmp/github_event.json',
            'GITHUB_WORKSPACE': workspace,
            'GITHUB_SHA': scm.get_sha(),
            'GITHUB_REF': scm.get_ref()
        }

        for e in dict(env):
            env.update({e.replace('GITHUB_', 'POPPER_'): env[e]})

        return env

    def run(self, action, skip_clone, skip_pull, skip, workspace,
            reuse, dry_run, parallel, with_dependencies, runtime,
            skip_secrets_prompt=False):
        """Run the workflow or a specific action.
        """
        new_wf = deepcopy(self.wf)

        if skip:
            new_wf = Workflow.skip_actions(self.wf, skip)

        if action:
            new_wf = Workflow.filter_action(self.wf, action, with_dependencies)

        new_wf.check_for_unreachable_actions(skip)

        WorkflowRunner.check_secrets(new_wf, dry_run, skip_secrets_prompt)
        WorkflowRunner.download_actions(new_wf, dry_run, skip_clone, self.wid)
        WorkflowRunner.instantiate_runners(
            runtime, new_wf, workspace, dry_run, skip_pull, self.wid)

        for s in new_wf.get_stages():
            WorkflowRunner.run_stage(new_wf, s, reuse, parallel)

    @staticmethod
    def run_stage(wf, stage, reuse=False, parallel=False):
        """Runs actions in a stage either parallely or
        sequentially."""
        if parallel:
            with ProcessPoolExecutor(max_workers=mp.cpu_count()) as ex:
                flist = {
                    ex.submit(wf.action[a]['runner'].run, reuse):
                        a for a in stage
                }
                popper.cli.flist = flist
                for future in as_completed(flist):
                    future.result()
        else:
            for a in stage:
                wf.action[a]['runner'].run(reuse)


class ActionRunner(object):
    """An action runner.
    """

    def __init__(self, action, workspace, env, dry_run, skip_pull, wid):
        self.action = action
        self.workspace = workspace
        self.env = env
        self.dry_run = dry_run
        self.skip_pull = skip_pull
        self.wid = wid
        self.msg_prefix = "DRYRUN: " if dry_run else ""
        self.setup_necessary_files()

    def handle_exit(self, ecode):
        """Exit handler for the action.

        Args:
            ecode (int): The exit code of the action's process.
        """
        if ecode == 0:
            log.info(
                "Action '{}' ran successfully !".format(
                    self.action['name']))
        elif ecode == 78:
            log.info(
                "Action '{}' ran successfully !".format(
                    self.action['name']))
            os.kill(os.getpid(), signal.SIGUSR1)
        else:
            log.fail("Action '{}' failed !".format(self.action['name']))

    def check_executable(self, command):
        """Check whether the required executable dependencies
        are installed in the system or not.

        Args:
            command (str): The command to check for.
        """
        if not find_executable(command):
            log.fail(
                'Could not find the {} command.'.format(command)
            )

    def setup_necessary_files(self):
        """Setup necessary files and folders for an action.
        """
        if not os.path.exists(self.workspace):
            os.makedirs(self.workspace)

        if not os.path.exists(self.env['GITHUB_EVENT_PATH']):
            f = open(self.env['GITHUB_EVENT_PATH'], 'w')
            f.close()

    def prepare_environment(self, set_env=False):
        """Prepare the environment variables to be
        set while running an action.

        Args:
            set_env (bool): If True, the environment gets
                            added to the current shell.
                            Default value is False.

        Returns:
            dict: The environment variables dict.
        """
        env = self.action.get('env', {})

        for s in self.action.get('secrets', []):
            env.update({s: os.environ[s]})

        for e, v in self.env.items():
            env.update({e: v})

        env['GITHUB_ACTION'] = self.action['name']
        env['POPPER_ACTION'] = self.action['name']

        if set_env:
            for k, v in env.items():
                os.environ[k] = v

        return env

    def remove_environment(self):
        """Removes the runtime environment variables.
        """
        env = self.prepare_environment()
        env.pop('HOME')
        for k, v in env.items():
            os.environ.pop(k, None)

    def run(self, reuse=False):
        raise NotImplementedError(
            "This method is required to be implemented in derived classes."
        )


class DockerRunner(ActionRunner):
    """Run a Github Action in Docker runtime.
    """

    def __init__(self, action, workspace, env, dry, skip_pull, wid):
        super(DockerRunner, self).__init__(
            action, workspace, env, dry, skip_pull, wid)
        self.cid = pu.sanitized_name(self.action['name'], wid)
        self.container = None

    def get_build_resources(self):
        """Parse the `uses` attribute and get the build resources
        from them.

        Returns:
            (bool, str, str): pull/build, image ref, the build source
        """
        build = True
        image = None
        build_source = None

        if 'docker://' in self.action['uses']:
            image = self.action['uses'].replace('docker://', '')
            if ':' not in image:
                image += ":latest"
            build = False

        elif './' in self.action['uses']:
            action_dir = os.path.basename(
                self.action['uses'].replace('./', ''))

            if self.env['GITHUB_REPOSITORY'] == 'unknown':
                repo_id = ''
            else:
                repo_id = self.env['GITHUB_REPOSITORY']

                if action_dir:
                    repo_id += '/'

            image = repo_id + action_dir + ':' + self.env['GITHUB_SHA']

            build_source = os.path.join(
                scm.get_git_root_folder(), self.action['uses'])
        else:
            _, _, user, repo, _, version = scm.parse(self.action['uses'])
            image = '{}/{}:{}'.format(user, repo, version)
            build_source = os.path.join(self.action['repo_dir'],
                                        self.action['action_dir'])

        image = image.lower()
        return (build, image, build_source)

    def run(self, reuse=False):
        """Parent function to handle the execution of an
        action.

        Args:
            reuse (bool): Whether to reuse existent containers or not.
        """
        self.check_executable('docker')
        build, image, build_source = self.get_build_resources()

        if not reuse:
            if self.docker_exists():
                self.docker_rm()
            if build:
                self.docker_build(image, build_source)
            else:
                self.docker_pull(image)
            self.docker_create(image)
        else:
            if not self.docker_exists():
                if build:
                    self.docker_build(image, build_source)
                else:
                    self.docker_pull(image)
                self.docker_create(image)
            else:
                self.container.commit(self.cid, 'reuse')
                self.docker_rm()
                self.docker_create('{}:reuse'.format(self.cid))

        if self.container is not None:
            popper.cli.docker_list.append(self.container)

        e = self.docker_start()
        self.handle_exit(e)

    def docker_exists(self):
        """Check whether the container exists or not.

        Returns:
            bool: Whether the container exists or not.
        """
        if self.dry_run:
            return True
        containers = docker_client.containers.list(
            all=True, filters={'name': self.cid})

        filtered_containers = [c for c in containers if c.name == self.cid]
        if len(filtered_containers):
            self.container = filtered_containers[0]
            return True

        return False

    def docker_image_exists(self, img):
        """Check whether a docker image exists or not.

        Args:
            img (str): The image to check for.

        Returns:
            bool: Whether the image exists or not.
        """
        if self.dry_run:
            return True
        images = docker_client.images.list(all=True)
        filtered_images = [i for i in images if img in i.tags]
        if filtered_images:
            return True

        return False

    def docker_rm(self):
        """Remove the docker container.
        """
        if self.dry_run:
            return
        self.container.remove(force=True)

    def docker_create(self, img):
        """Create a docker container from an image.

        Args:
            img (str): The image to use for building the container.
        """
        log.info('{}[{}] docker create {} {}'.format(
            self.msg_prefix,
            self.action['name'], img, ' '.join(self.action.get('args', ''))
        ))
        if self.dry_run:
            return

        env = self.prepare_environment()

        volumes = [
            '/var/run/docker.sock:/var/run/docker.sock',
            '{}:{}'.format(env['HOME'], env['HOME']),
            '{}:{}'.format(env['HOME'], '/github/home'),
            '{}:{}'.format(env['GITHUB_WORKSPACE'],
                           env['GITHUB_WORKSPACE']),
            '{}:{}'.format(env['GITHUB_WORKSPACE'], '/github/workspace'),
            '{}:{}'.format(env['GITHUB_EVENT_PATH'],
                           '/github/workflow/event.json')
        ]

        self.container = docker_client.containers.create(
            image=img,
            command=self.action.get('args', None),
            name=self.cid,
            volumes=volumes,
            working_dir=env['GITHUB_WORKSPACE'],
            environment=env,
            entrypoint=self.action.get('runs', None),
            detach=True
        )

    def docker_start(self):
        """Start the container process.

        Returns:
            int: The returncode of the container process.
        """
        log.info('{}[{}] docker start '.format(self.msg_prefix,
                                               self.action['name']))
        if self.dry_run:
            return 0
        self.container.start()
        cout = self.container.logs(stream=True)
        for line in cout:
            log.action_info(pu.decode(line).strip('\n'))

        return self.container.wait()['StatusCode']

    def docker_pull(self, img):
        """Pull an image from Dockerhub.

        Args:
            img (str): The image reference to pull.
        """
        if not self.skip_pull:
            log.info('{}[{}] docker pull {}'.format(self.msg_prefix,
                                                    self.action['name'], img))
            if self.dry_run:
                return
            docker_client.images.pull(repository=img)
        else:
            if not self.docker_image_exists(img):
                log.fail(
                    'The required docker image \'{}\' was not found '
                    'locally.' .format(img))

    def docker_build(self, img, path):
        """Build a docker image from a Dockerfile.

        Args:
            img (str): The name of the image to build.
            path (str): The path to the Dockerfile and other resources.
        """
        log.info('{}[{}] docker build -t {} {}'.format(
            self.msg_prefix, self.action['name'], img, path))
        if self.dry_run:
            return
        docker_client.images.build(path=path, tag=img, rm=True, pull=True)


class SingularityRunner(ActionRunner):
    """Runs a Github Action in Singularity runtime.
    """

    def __init__(self, action, workspace, env, dry_run, skip_pull, wid):
        super(SingularityRunner, self).__init__(action, workspace, env,
                                                dry_run, skip_pull, wid)
        s_client.quiet = True

    @staticmethod
    def setup_singularity_cache(wid):
        """Setup the singularity cache directory based
        on the workflow id.

        Args:
            wid (str): The workflow id.

        Returns:
            str: The path to the cache dir.
        """
        singularity_cache = os.path.join(
            pu.setup_base_cache(), 'singularity', wid)
        if not os.path.exists(singularity_cache):
            os.makedirs(singularity_cache)
        return singularity_cache

    def get_build_resources(self):
        """Parse the `uses` attribute and get the build
        resources from them.

        Args:
            (bool, str, str): pull/build, image ref, the build source.
        """
        build = True
        image = None
        build_source = None

        if 'docker://' in self.action['uses']:
            image = self.action['uses']
            build = False

        elif './' in self.action['uses']:
            image = 'action/' + self.action['uses']
            build_source = os.path.join(
                scm.get_git_root_folder(), self.action['uses'])

        else:
            image = self.action['uses']
            build_source = os.path.join(
                self.action['repo_dir'], self.action['action_dir'])

        return (build, image, build_source)

    def run(self, reuse=False):
        """Parent function to handle the execution
        of the action.

        Args:
            reuse (bool): Whether to reuse containers or not.
        """
        self.check_executable('singularity')
        singularity_cache = SingularityRunner.setup_singularity_cache(self.wid)

        if reuse:
            log.fail('Reusing containers in singularity runtime is '
                     'currently not supported.')

        build, image, build_source = self.get_build_resources()

        container_path = os.path.join(
            singularity_cache, pu.sanitized_name(image, self.wid) + '.sif'
        )

        if build:
            self.singularity_build_from_recipe(build_source, container_path)
        else:
            self.singularity_build_from_image(image, container_path)

        e = self.singularity_start(container_path)
        self.handle_exit(e)

    @staticmethod
    def convert(dockerfile, singularityfile):
        """Convert a Dockerfile to a Singularity recipe file.

        Args:
            dockerfile (str): The path to the Dockerfile.
            singularityfile (str): The path to the Singularity recipe.

        Returns:
            str: The Singularity recipefile path.
        """
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

    @staticmethod
    def get_recipe_file(build_source, wid):
        """Get the Singularity recipe file from the build source.

        Finds out a Dockerfile from the build source and
        converts it to Singularity recipe. If no Dockerfile is
        found, it simply fails.

        Args:
            build_source (str): The path to the build source.
            wid (str): The workflow id to use while naming the
                        Singularity recipefile.

        Returns:
            str: The path to the Singularity recipefile.
        """
        dockerfile = os.path.join(build_source, 'Dockerfile')
        singularityfile = os.path.join(
            build_source, 'Singularity.{}'.format(wid))

        if os.path.isfile(dockerfile):
            return SingularityRunner.convert(dockerfile, singularityfile)
        else:
            log.fail('No Dockerfile was found.')

    @staticmethod
    def build_from_recipe(build_source, build_dest, container, wid):
        """Helper function to build the singularity image.

        Args:
            build_source (str): The source dir from where to build the
                                container image.
            build_dest (str): The destination dir where to put the built
                              container image.
            container (str): The name of the container image.
            wid (str): The workflow id.
        """
        pwd = os.getcwd()
        os.chdir(build_source)
        recipefile = SingularityRunner.get_recipe_file(build_source, wid)
        s_client.build(
            recipe=recipefile,
            image=container,
            build_folder=build_dest)
        os.chdir(pwd)

    def singularity_exists(self, container_path):
        """Check whether the container exists or not.

        Args:
            container_path (str): The path where to check for
            the container.

        Returns:
            bool: Whether the container already exists or not.
        """
        if self.dry_run:
            return
        return os.path.exists(container_path)

    def singularity_rm(self, container_path):
        """Remove the container.

        Args:
            container_path (str): The path to the container to remove.
        """
        if self.dry_run:
            return
        os.remove(container_path)

    def singularity_build_from_image(self, image, container_path):
        """Build a container from Docker image.

        Args:
            image (str): The docker image to build the container from.
            container_path (str): The path of the built container.
        """
        container = os.path.basename(container_path)

        if not self.skip_pull:
            log.info('{}[{}] singularity pull {} {}'.format(
                self.msg_prefix, self.action['name'], container, image)
            )
            if not self.dry_run:
                if not self.singularity_exists(container_path):
                    s_client.pull(
                        image=image,
                        name=container,
                        pull_folder=os.path.dirname(container_path))
        else:
            if not self.singularity_exists(container_path):
                log.fail(
                    'The required singularity container \'{}\' was not found '
                    'locally.'.format(container_path))

    def singularity_build_from_recipe(
            self, build_source, container_path):
        """Builds a container image from a recipefile.

        Args:
            build_source (str): The path to the build source,
            which contains all the resources required to build the
            Docker image.

            container_path (str): The path of the built container.
        """
        container = os.path.basename(container_path)
        recipefile = os.path.join(
            build_source,
            'Singularity.{}'.format(self.wid))
        build_dest = os.path.dirname(container_path)

        log.info('{}[{}] singularity build {} {}'.format(
            self.msg_prefix, self.action['name'],
            container, recipefile)
        )

        if not self.dry_run:
            if not self.singularity_exists(container_path):
                SingularityRunner.build_from_recipe(
                    build_source, build_dest, container, self.wid)

    def singularity_start(self, container_path):
        """Starts the container to execute commands or run the runscript
        with the supplied args inside the container.

        Args:
            container_path (str): The container image to run/execute.

        Returns:
            int: The container process returncode.
        """
        env = self.prepare_environment(set_env=True)

        volumes = [
            '{}:{}'.format(env['HOME'], env['HOME']),
            '{}:{}'.format(env['HOME'], '/github/home'),
            '{}:{}'.format(env['GITHUB_WORKSPACE'],
                           env['GITHUB_WORKSPACE']),
            '{}:{}'.format(env['GITHUB_WORKSPACE'], '/github/workspace'),
            '{}:{}'.format(env['GITHUB_EVENT_PATH'],
                           '/github/workflow/event.json')
        ]

        args = self.action.get('args', None)
        runs = self.action.get('runs', None)
        ecode = None

        if runs:
            info = '{}[{}] singularity exec {} {}'.format(
                self.msg_prefix, self.action['name'],
                container_path, runs)
            commands = runs
            start = s_client.execute
        else:
            info = '{}[{}] singularity run {} {}'.format(
                self.msg_prefix, self.action['name'],
                container_path, args)
            commands = args
            start = s_client.run

        log.info(info)
        if not self.dry_run:
            output = start(container_path, commands, bind=volumes,
                           stream=True, options=[
                               '--userns',
                               '--pwd', env['GITHUB_WORKSPACE']])
            try:
                for line in output:
                    log.action_info(line)
                ecode = 0
            except subprocess.CalledProcessError as ex:
                ecode = ex.returncode
        else:
            ecode = 0

        self.remove_environment()
        return ecode


class HostRunner(ActionRunner):
    """
    Run an Action on the Host Machine.
    """

    def __init__(self, action, workspace, env, dry, skip_pull, wid):
        super(HostRunner, self).__init__(
            action, workspace, env, dry, skip_pull, wid)
        self.cwd = os.getcwd()

    def run(self, reuse=False):
        if reuse:
            log.fail('--reuse flag is not supported for actions running '
                     'on the host.')

        cmd = self.host_prepare()
        self.prepare_environment(set_env=True)
        e = self.host_start(cmd)
        self.remove_environment()
        self.handle_exit(e)

    def host_prepare(self):
        """Prepare the commands and environment to start execution.

        Returns:
            str: The command to execute.
        """
        root = scm.get_git_root_folder()
        if self.action['uses'] == 'sh':
            cmd = self.action.get('runs', [])
            if cmd:
                cmd[0] = os.path.join(root, cmd[0])
            cmd.extend(self.action.get('args', []))

            if not self.dry_run:
                os.chdir(root)
        else:
            cmd = self.action.get('runs', ['entrypoint.sh'])
            cmd[0] = os.path.join('./', cmd[0])
            cmd.extend(self.action.get('args', []))

            if not self.dry_run:
                if 'repo_dir' in self.action:
                    os.chdir(self.action['repo_dir'])
                    cmd[0] = os.path.join(self.action['repo_dir'], cmd[0])
                else:
                    os.chdir(os.path.join(root, self.action['uses']))
                    cmd[0] = os.path.join(root, self.action['uses'], cmd[0])

        return cmd

    def host_start(self, cmd):
        """Start the execution of the command on the host machine.

        Args:
            cmd (str): The command to execute.
        Returns:
            int: The returncode of the process.
        """
        log.info('{}[{}] {}'.format(self.msg_prefix, self.action['name'],
                                    ' '.join(cmd)))

        if self.dry_run:
            return 0

        ecode = 0

        try:
            log.debug('Executing: {}'.format(' '.join(cmd)))
            p = Popen(' '.join(cmd), stdout=PIPE, stderr=STDOUT, shell=True,
                      universal_newlines=True, preexec_fn=os.setsid)

            popper.cli.process_list.append(p.pid)

            log.debug('Reading process output')

            for line in iter(p.stdout.readline, ''):
                line_decoded = pu.decode(line)
                log.action_info(line_decoded[:-1])

            p.wait()
            ecode = p.poll()
            log.debug('Code returned by process: {}'.format(ecode))

        except CalledProcessError as ex:
            msg = "Command '{}' failed: {}".format(cmd, ex)
            ecode = ex.returncode
            log.action_info(msg)
        finally:
            log.action_info()

        os.chdir(self.cwd)
        return ecode
