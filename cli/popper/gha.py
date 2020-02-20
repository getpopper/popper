from __future__ import unicode_literals
import os
import signal
import time
import getpass
import threading
import subprocess
import multiprocessing as mp
from copy import deepcopy
from builtins import dict
from distutils.spawn import find_executable
from concurrent.futures import (ThreadPoolExecutor,
                                as_completed)
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
s_client = spython.main.Client


class WorkflowRunner(object):
    """A GHA workflow runner."""

    def __init__(self, workflow):
        self.wf = workflow
        self.wf.parse()
        self.wid = pu.get_id(os.getuid(), self.wf.wfile)
        log.debug('workflow:\n{}'.format(
            yaml.dump(self.wf, default_flow_style=False, default_style='')))

    @staticmethod
    def check_secrets(wf, dry_run, skip_secrets_prompt):
        """Checks whether the secrets defined for a step block is set in the
        execution environment or not.

        Note:
            When the environment variable `CI` is set to `true`,
            then the execution fails if secrets are not defined
            else it prompts the user to enter the environment vars
            during the time of execution itself.

        Args:
          wf(popper.parser.workflow): Instance of the Workflow class.
          dry_run(bool): True if workflow flag is
                        being dry-run.
          skip_secrets_prompt(bool): True if part of the workflow
                        has to be skipped.

        Returns:
            None
        """
        if dry_run or skip_secrets_prompt:
            return
        for _, a in wf.step.items():
            for s in a.get('secrets', []):
                if s not in os.environ:
                    if os.environ.get('CI') == 'true':
                        log.fail('Secret {} not defined'.format(s))
                    else:
                        val = getpass.getpass(
                            'Enter the value for {} : '.format(s))
                        os.environ[s] = val

    @staticmethod
    def clone_repos(wf, dry_run, skip_clone, wid):
        """Clone steps that reference a repository.

        Args:
          wf(popper.parser.workflow): Instance of the Workflow class.
          dry_run(bool): True if workflow flag is being dry-run.
          skip_clone(bool): True if clonning step has to be skipped.
          wid(str):

        Returns:
            None
        """
        repo_cache = os.path.join(pu.setup_base_cache(), wid)

        cloned = set()
        infoed = False

        for _, a in wf.step.items():
            uses = a['uses']
            if 'docker://' in uses or './' in uses or uses == 'sh':
                continue

            url, service, user, repo, step_dir, version = scm.parse(
                a['uses'])

            repo_dir = os.path.join(repo_cache, service, user, repo)

            a['repo_dir'] = repo_dir
            a['step_dir'] = step_dir

            if dry_run:
                continue

            if skip_clone:
                if not os.path.exists(repo_dir):
                    log.fail(
                        'The required step folder \'{}\' was not '
                        'found locally.'.format(repo_dir))
                continue

            if not infoed:
                log.info('[popper] Cloning step repositories')
                infoed = True

            if '{}/{}'.format(user, repo) in cloned:
                continue

            log.info('[popper] - {}/{}/{}@{}'.format(url, user, repo, version))
            scm.clone(url, user, repo, repo_dir, version)
            cloned.add('{}/{}'.format(user, repo))

    @staticmethod
    def instantiate_runners(engine, wf, workspace, dry_run, skip_pull, wid,
                            engine_conf=None):
        """Factory of StepRunner instances, one for each step.

        Note:
            If the `uses` attribute startswith a './' and does not have
            a `Dockerfile` in the referenced directory, we assume that
            it is meant to be run on the Host machine and ignore the
            engine argument.
            Same is the case when the `uses` attribute is equal to 'sh'.

        Args:
          runtime(str): Identifier of the workflow being executed.
          wf(popper.parser.workflow): Instance of the Workflow class.
          workspace(str): Location of the workspace.
          dry_run(bool): True if workflow flag is being dry-run.
          skip_pull(bool): True if pulling step has to be skipped.
          wid(str):

        Returns:
            None
        """
        for _, a in wf.step.items():

            if a['uses'] == 'sh':
                a['runner'] = HostRunner(
                    a, workspace, dry_run, skip_pull, wid, engine_conf)
                continue

            if a['uses'].startswith('./'):
                if not os.path.isfile(
                    os.path.join(scm.get_git_root_folder(), a['uses'],
                                 'Dockerfile')):

                    a['runner'] = HostRunner(
                        a, workspace, dry_run, skip_pull, wid,
                        engine_conf)
                    continue

            if engine == 'docker':
                a['runner'] = DockerRunner(
                    a, workspace, dry_run, skip_pull, wid, engine_conf)

            elif engine == 'singularity':
                a['runner'] = SingularityRunner(
                    a, workspace, dry_run, skip_pull, wid, engine_conf)

            elif engine == 'vagrant':
                a['runner'] = VagrantRunner(
                    a, workspace, dry_run, skip_pull, wid, engine_conf)

    def run(self, step, skip_clone, skip_pull, skip, workspace,
            reuse, dry_run, parallel, with_dependencies, engine,
            conf, skip_secrets_prompt=False):
        """Run the workflow or a specific step.

        Args:
          step(str): Name of particular step being executed from workflow.
          skip_clone(bool): True if cloning step has to be skipped.
          skip_pull(bool): True if pulling step has to be skipped.
          skip(tuple): Tuple containing the steps to be skipped.
          workspace(str): Location of the workspace.
          reuse(bool): True if existing containers are to be reused.
          dry_run(bool): True if workflow flag is being dry-run.
          parallel(bool): True if steps are to be executed in parallel.
          with_dependencies(bool): True if with-dependencies flag is passed
                                    as an argument.
          runtime(str): Name of the run time being used in workflow.
          skip_secrets_prompt(bool): True if part of the workflow has to
                                    be skipped.(Default value = False)

        Returns:
            None
        """
        new_wf = deepcopy(self.wf)

        if skip:
            new_wf = Workflow.skip_steps(self.wf, skip)

        if step:
            new_wf = Workflow.filter_step(self.wf, step, with_dependencies)

        engine_conf = pu.parse_engine_configuration(conf)

        new_wf.check_for_unreachable_steps(skip)

        WorkflowRunner.check_secrets(new_wf, dry_run, skip_secrets_prompt)
        WorkflowRunner.clone_repos(new_wf, dry_run, skip_clone, self.wid)
        WorkflowRunner.instantiate_runners(
            engine,
            new_wf,
            workspace,
            dry_run,
            skip_pull,
            self.wid,
            engine_conf=engine_conf)

        for s in new_wf.get_stages():
            log.debug(s)
            WorkflowRunner.run_stage(
                engine, new_wf, s, reuse, parallel)

    @staticmethod
    def run_stage(engine, wf, stage, reuse=False,
                  parallel=False):
        """Runs steps in a stage either parallelly or sequentially.

        Args:
          engine(str): Name of container engine to use for the workflow.
          wf(popper.parser.Workflow): Instance of the Workflow class.
          stage(set): Set containing stages to be executed in the workflow.
          reuse(bool): True if existing containers are to be
                        reused.(Default value = False).
          parallel(bool): True if parallel flag is passed as an
                        argument(Default value = False).

        Returns:
            None
        """
        if parallel:
            with ThreadPoolExecutor(max_workers=mp.cpu_count()) as ex:
                flist = {
                    ex.submit(
                        wf.step[a]['runner'].run,
                        reuse): a for a in stage}
                popper.cli.flist = flist
                for future in as_completed(flist):
                    future.result()
        else:
            for a in stage:
                wf.step[a]['runner'].run(reuse)


class StepRunner(object):
    """An step runner."""

    def __init__(self, step, workspace, dry_run, skip_pull, wid, engine_conf):
        self.step = step
        self.workspace = workspace
        self.dry_run = dry_run
        self.skip_pull = skip_pull
        self.wid = wid
        self.engine_conf = engine_conf
        self.msg_prefix = "DRYRUN: " if dry_run else ""
        self.setup_necessary_files()

    def handle_exit(self, ecode):
        """Exit handler for the step.

        Args:
          ecode(int): The exit code of the step's process.

        Returns:
            None
        """
        if ecode == 0:
            log.info("Step '{}' ran successfully !".format(self.step['name']))
        elif ecode == 78:
            log.info("Step '{}' ran successfully !".format(self.step['name']))
            os.kill(os.getpid(), signal.SIGUSR1)
        else:
            log.fail("Step '{}' failed !".format(self.step['name']))

    def check_executable(self, command):
        """Check whether the required executable dependencies are installed in
        the system or not.

        Args:
          command(str): The command to check for.

        Returns:
            None
        """
        if not find_executable(command):
            log.fail(
                'Could not find the {} command.'.format(command)
            )

    def setup_necessary_files(self):
        """Setup necessary files and folders for an step.

        Args:
            None

        Returns:
            None
        """
        if not os.path.exists(self.workspace):
            os.makedirs(self.workspace)

    def prepare_volumes(self, include_docker_socket=False):
        """Prepare volume bindings for the container.

        Args:
          include_docker_socket(bool): True if docker socket is included.

        Returns:
            list: Volume bindings.
        """
        volumes = ['{}:{}'.format(self.workspace, '/workspace')]
        if include_docker_socket:
            volumes.append('/var/run/docker.sock:/var/run/docker.sock')
        return volumes

    def prepare_environment(self):
        """Prepare the environment variables to be set while running an step.

        Args:
          set_env(bool, optional): If True, the environment gets
        added to the current shell.(Default value = False)

        Returns:
          dict: The environment variables dict.
        """
        env = self.step.get('env', {}).copy()

        for s in self.step.get('secrets', []):
            env.update({s: os.environ[s]})

        return env

    def run(self, reuse=False):
        """

        Args:
          reuse:True if existing containers are to be reused.
                (Default value = False)

        Returns:
            None

        """
        raise NotImplementedError(
            "This method is required to be implemented in derived classes."
        )


class DockerRunner(StepRunner):
    """Runs steps in docker."""

    def __init__(self, step, workspace, dry, skip_pull, wid, engine_conf):
        super(DockerRunner, self).__init__(
            step, workspace, dry, skip_pull, wid, engine_conf)
        self.d_client = docker.from_env()
        self.cid = pu.sanitized_name(self.step['name'], wid)
        self.container = None

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.d_client.close()

    def get_build_resources(self):
        """Parse the `uses` attribute and get the build resources from them.

        Args:
            None

        Returns:
          bool: pull/build, image ref, the build source
        """
        build = True
        image = None
        build_source = None

        if 'docker://' in self.step['uses']:
            image = self.step['uses'].replace('docker://', '')
            if ':' not in image:
                image += ":latest"
            build = False

        elif './' in self.step['uses']:
            image = pu.sanitized_name(self.step['name']) + ':' + scm.get_sha()
            build_source = os.path.join(
                scm.get_git_root_folder(), self.step['uses'])
        else:
            _, _, user, repo, _, version = scm.parse(self.step['uses'])
            image = '{}/{}:{}'.format(user, repo, version)
            build_source = os.path.join(self.step['repo_dir'],
                                        self.step['step_dir'])

        image = image.lower()
        return (build, image, build_source)

    def run(self, reuse=False):
        """Parent function to handle the execution of an step.

        Args:
          reuse(bool, optional): True if existing containers are to be reused.
                                (Default value = False)

        Returns:
            None
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

        Args:
            None

        Returns:
          bool: Whether the container exists or not.
        """
        if self.dry_run:
            return True
        containers = self.d_client.containers.list(
            all=True, filters={'name': self.cid})

        filtered_containers = [c for c in containers if c.name == self.cid]
        if len(filtered_containers):
            self.container = filtered_containers[0]
            return True

        return False

    def docker_image_exists(self, img):
        """Check whether a docker image exists or not.

        Args:
          img(str): The image to check for.

        Returns:
          bool: Whether the image exists or not.
        """
        if self.dry_run:
            return True
        images = self.d_client.images.list(all=True)
        filtered_images = [i for i in images if img in i.tags]
        if filtered_images:
            return True

        return False

    def docker_rm(self):
        """Remove the docker container."""
        if self.dry_run:
            return
        self.container.remove(force=True)

    def mix_with_engine_conf(self, engine_conf):
        engine_conf["volumes"] = [*engine_conf["volumes"],
                                  *self.engine_conf.get('volumes', list())]
        for k, v in self.engine_conf.get('environment', dict()).items():
            engine_conf["environment"].update({k: v})

        for k, v in self.engine_conf.items():
            if k not in engine_conf.keys():
                engine_conf[k] = self.engine_conf[k]
        return engine_conf

    def docker_create(self, img):
        """Create a docker container from an image.

        Args:
          img(str): The image to use for building the container.

        Returns:
            None
        """
        log.info('{}[{}] docker create {} {}'.format(
            self.msg_prefix,
            self.step['name'], img, ' '.join(self.step.get('args', ''))
        ))
        if self.dry_run:
            return

        env = self.prepare_environment()
        volumes = self.prepare_volumes(include_docker_socket=True)

        engine_conf = {
            "image": img,
            "command": self.step.get('args', None),
            "name": self.cid,
            "volumes": volumes,
            "working_dir": '/workspace',
            "environment": env,
            "entrypoint": self.step.get('runs', None),
            "detach": True
        }

        if self.engine_conf:
            engine_conf = self.mix_with_engine_conf(engine_conf)

        log.debug(engine_conf)
        self.container = self.d_client.containers.create(**engine_conf)

    def docker_start(self):
        """Start the container process.

        Args:
            None

        Returns:
          int: The returncode of the container process.
        """
        log.info('{}[{}] docker start '.format(self.msg_prefix,
                                               self.step['name']))
        if self.dry_run:
            return 0
        self.container.start()
        cout = self.container.logs(stream=True)
        for line in cout:
            log.step_info(pu.decode(line).strip('\n'))

        return self.container.wait()['StatusCode']

    def docker_pull(self, img):
        """Pull an image from Dockerhub.

        Args:
          img(str): The image reference to pull.

        Returns:
            None
        """
        if not self.skip_pull:
            log.info('{}[{}] docker pull {}'.format(self.msg_prefix,
                                                    self.step['name'], img))
            if self.dry_run:
                return
            self.d_client.images.pull(repository=img)
        else:
            if not self.docker_image_exists(img):
                log.fail(
                    'The required docker image \'{}\' was not found '
                    'locally.' .format(img))

    def docker_build(self, img, path):
        """Build a docker image from a Dockerfile.

        Args:
          img(str): The name of the image to build.
          path(str): The path to the Dockerfile and other resources.

        Returns:
            None
        """
        log.info('{}[{}] docker build -t {} {}'.format(
            self.msg_prefix, self.step['name'], img, path))
        if self.dry_run:
            return
        self.d_client.images.build(path=path, tag=img, rm=True, pull=True)


class SingularityRunner(StepRunner):
    """Runs steps in singularity."""
    lock = threading.Lock()

    def __init__(self, step, workspace, dry_run, skip_pull, wid, engine_conf):
        super(SingularityRunner, self).__init__(
            step, workspace, dry_run, skip_pull, wid, engine_conf)
        s_client.quiet = True

    @staticmethod
    def setup_singularity_cache(wid):
        """Setup the singularity cache directory based on the workflow id.

        Args:
          wid(str): The workflow id.

        Returns:
          str: The path to the cache dir.
        """
        singularity_cache = os.path.join(
            pu.setup_base_cache(), 'singularity', wid)
        if not os.path.exists(singularity_cache):
            os.makedirs(singularity_cache, exist_ok=True)
        return singularity_cache

    def get_build_resources(self):
        """Parse the `uses` attribute and get the build resources from them.

        Args:
          (bool,str,str): pull/build, image ref, the build source.

        Returns:
            tuple : containing build,image and build_source.
        """
        build = True
        image = None
        build_source = None

        if 'docker://' in self.step['uses']:
            image = self.step['uses']
            build = False

        elif './' in self.step['uses']:
            image = pu.sanitized_name(self.step['name']) + ':' + scm.get_sha()
            build_source = os.path.join(scm.get_git_root_folder(),
                                        self.step['uses'])
        else:
            image = self.step['uses']
            build_source = os.path.join(
                self.step['repo_dir'], self.step['step_dir'])

        return (build, image, build_source)

    def run(self, reuse=False):
        """Parent function to handle the execution of the step.

        Args:
          reuse(bool, optional): True if existing containers are
                            to be reused.(Default value = False)

        Returns:
            None
        """
        self.check_executable('singularity')
        singularity_cache = SingularityRunner.setup_singularity_cache(self.wid)

        if reuse:
            log.fail('Reusing containers in singularity engine is '
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
          dockerfile(str): The path to the Dockerfile.
          singularityfile(str): The path to the Singularity recipe.

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
          build_source(str): The path to the build source.
          wid(str): The workflow id to use while naming the
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
          build_source(str): The source dir from where to build the
        container image.
          build_dest(str): The destination dir where to put the built
        container image.
          container(str): The name of the container image.
          wid(str): The workflow id.

        Returns:
            None
        """
        SingularityRunner.lock.acquire()
        pwd = os.getcwd()
        os.chdir(build_source)
        recipefile = SingularityRunner.get_recipe_file(build_source, wid)
        s_client.build(
            recipe=recipefile,
            image=container,
            build_folder=build_dest)
        os.chdir(pwd)
        SingularityRunner.lock.release()

    def singularity_exists(self, container_path):
        """Check whether the container exists or not.

        Args:
          container_path(str): The path where to check for
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
          container_path(str): The path to the container to remove.

        Returns:
            None
        """
        if self.dry_run:
            return
        os.remove(container_path)

    def singularity_build_from_image(self, image, container_path):
        """Build a container from Docker image.

        Args:
          image(str): The docker image to build the container from.
          container_path(str): The path of the built container.

        Returns:
            None
        """
        container = os.path.basename(container_path)

        if not self.skip_pull:
            log.info('{}[{}] singularity pull {} {}'.format(
                self.msg_prefix, self.step['name'], container, image)
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
          build_source(str): The path to the build source,
        which contains all the resources required to build the
        Docker image.
        container_path(str): The path of the built container.
          container_path:

        Returns:
            None
        """
        container = os.path.basename(container_path)
        recipefile = os.path.join(
            build_source,
            'Singularity.{}'.format(self.wid))
        build_dest = os.path.dirname(container_path)

        log.info('{}[{}] singularity build {} {}'.format(
            self.msg_prefix, self.step['name'],
            container, recipefile)
        )

        if not self.dry_run:
            if not self.singularity_exists(container_path):
                SingularityRunner.build_from_recipe(
                    build_source, build_dest, container, self.wid)

    def singularity_start(self, container_path):
        """Starts the container to execute commands or run the runscript with
        the supplied args inside the container.

        Args:
          container_path(str): The container image to run/execute.

        Returns:
          int: The container process returncode.
        """
        volumes = self.prepare_volumes()

        args = self.step.get('args', None)
        runs = self.step.get('runs', None)
        ecode = None

        if runs:
            info = '{}[{}] singularity exec {} {}'.format(
                self.msg_prefix, self.step['name'],
                container_path, runs)
            commands = runs
            start = s_client.execute
        else:
            info = '{}[{}] singularity run {} {}'.format(
                self.msg_prefix, self.step['name'],
                container_path, args)
            commands = args
            start = s_client.run

        log.info(info)

        if self.dry_run:
            return 0

        curr_env = os.environ.copy()
        os.environ.update(self.prepare_environment())
        output = start(container_path, commands, bind=volumes, stream=True,
                       options=['--userns', '--pwd=/workspace'])
        try:
            for line in output:
                log.step_info(line)
            ecode = 0
        except subprocess.CalledProcessError as ex:
            ecode = ex.returncode
        else:
            ecode = 0

        os.environ = curr_env

        return ecode


class VagrantRunner(DockerRunner):
    """Runs steps in docker within a VM."""
    steps = set()
    running = False
    vbox_path = None
    lock = threading.Lock()
    vagrantfile_content = """
    Vagrant.configure("2") do |config|
        config.vm.box = "ailispaw/barge"
        config.vm.synced_folder "{}", "{}"
        config.vm.synced_folder "{}", "{}"
    end
    """

    def __init__(self, step, workspace, dry, skip_pull, wid, engine_conf):
        super(VagrantRunner, self).__init__(
            step, workspace, dry, skip_pull, wid, engine_conf
        )
        self.cid = pu.sanitized_name(self.step['name'], wid)
        VagrantRunner.steps.add(self.step['name'])

    @staticmethod
    def setup_vagrant_cache(wid):
        """Setup the vagrant cache directory based on the workflow id.

        Args:
          wid(str): The workflow id.

        Returns:
          str: The path to the cache dir.
        """
        vagrant_cache = os.path.join(
            pu.setup_base_cache(), 'vagrant', wid)
        if not os.path.exists(vagrant_cache):
            os.makedirs(vagrant_cache)
        return vagrant_cache

    def vagrant_write_vagrantfile(self, vagrant_box_path):
        """Bootstrap the Vagrantfile required to start the VM.

        Args:
          vagrant_box_path(str): The path to Vagrant VM's root.

        Returns:
            None
        """
        if self.dry_run:
            return
        if not os.path.exists(vagrant_box_path):
            os.makedirs(vagrant_box_path)
        vagrantfile_content = VagrantRunner.vagrantfile_content.format(
            os.environ['HOME'], os.environ['HOME'],
            self.workspace, self.workspace)
        pu.write_file(os.path.join(
            vagrant_box_path, 'Vagrantfile'), vagrantfile_content)

    def vagrant_exists(self, vagrant_box_path):
        """Check whether a vagrant VM already exists in running state in the
        specified path.

        Args:
          vagrant_box_path(str): The path to Vagrant VM's root.

        Returns:
          bool: Whether the VM exists in running state or not.
        """
        import vagrant

        if self.dry_run:
            return True
        vg_file_path = os.path.join(vagrant_box_path, 'Vagrantfile')
        if os.path.exists(vg_file_path):
            if vagrant.Vagrant(vagrant_box_path).status()[0].state == 'running':
                return True
        return False

    def vagrant_start(self, vagrant_box_path):
        """Start a Vagrant VM at the specified path.

        Args:
          vagrant_box_path(str): The path to Vagrant VM's root.

        Returns:
            None
        """
        import vagrant
        if self.dry_run:
            return
        if not self.vagrant_exists(vagrant_box_path):
            v = vagrant.Vagrant(root=vagrant_box_path)
            log.info("[+] Starting Virtual machine....")
            v.up()
            popper.cli.vagrant_list.append(vagrant_box_path)
            time.sleep(5)

    def vagrant_stop(self, vagrant_box_path):
        """Stop the Vagrant VM running at the specified path.

        Args:
          vagrant_box_path(str): The path to Vagrant VM's root.

        Returns:
            None
        """
        import vagrant
        if self.dry_run:
            return
        log.info("[-] Stopping VM....")
        vagrant.Vagrant(root=vagrant_box_path).halt()
        time.sleep(5)

    def run(self, reuse=False):
        """Parent function to handle the execution of the step.

        Args:
          reuse(bool, optional): True if existing containers are
                            to be reused.(Default value = False)

        Returns:
            None
        """
        self.check_executable('vagrant')
        self.check_executable('virtualbox')

        VagrantRunner.lock.acquire()
        if not VagrantRunner.running:
            VagrantRunner.vbox_path = VagrantRunner.setup_vagrant_cache(
                self.wid)
            self.vagrant_write_vagrantfile(VagrantRunner.vbox_path)
            self.vagrant_start(VagrantRunner.vbox_path)
            VagrantRunner.running = True
        VagrantRunner.lock.release()

        self.d_client = docker.DockerClient(
            base_url='tcp://0.0.0.0:2375',
            version='1.22',
            timeout=120)

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
        VagrantRunner.steps.remove(self.step['name'])

        # If all the steps are done, stop the VM
        if len(VagrantRunner.steps) == 0 and e != 78:
            self.vagrant_stop(VagrantRunner.vbox_path)
            VagrantRunner.running = False

        self.handle_exit(e)


class HostRunner(StepRunner):
    """Run an step on the Host Machine."""

    def __init__(self, step, workspace, dry, skip_pull, wid, engine_conf):
        super(HostRunner, self).__init__(
            step, workspace, dry, skip_pull, wid, engine_conf)
        self.cwd = os.getcwd()

    def run(self, reuse=False):
        """

        Args:
          reuse: True if existing containers are to be reused.
                (Default value = False)

        Returns:
            None

        """
        if reuse:
            log.fail('--reuse flag is not supported for steps running '
                     'on the host.')

        cmd = self.host_prepare()

        curr_env = os.environ.copy()
        os.environ = self.prepare_environment()

        e = self.host_start(cmd)

        os.environ = curr_env

        self.handle_exit(e)

    def host_prepare(self):
        """Prepare the commands and environment to start execution.

        Args:
            None

        Returns:
          str: The command to execute.
        """
        root = scm.get_git_root_folder()
        if self.step['uses'] == 'sh':
            cmd = self.step.get('runs', [])
            if cmd:
                cmd[0] = os.path.join(root, cmd[0])
            cmd.extend(self.step.get('args', []))

            if not self.dry_run:
                os.chdir(root)
        else:
            cmd = self.step.get('runs', ['entrypoint.sh'])
            cmd[0] = os.path.join('./', cmd[0])
            cmd.extend(self.step.get('args', []))

            if not self.dry_run:
                if 'repo_dir' in self.step:
                    os.chdir(self.step['repo_dir'])
                    cmd[0] = os.path.join(self.step['repo_dir'], cmd[0])
                else:
                    os.chdir(os.path.join(root, self.step['uses']))
                    cmd[0] = os.path.join(root, self.step['uses'], cmd[0])

        return cmd

    def host_start(self, cmd):
        """Start the execution of the command on the host machine.

        Args:
          cmd(str): The command to execute.

        Returns:
          int: The return code of the process.
        """
        log.info('{}[{}] {}'.format(self.msg_prefix, self.step['name'],
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
                log.step_info(line_decoded[:-1])

            p.wait()
            ecode = p.poll()
            log.debug('Code returned by process: {}'.format(ecode))

        except CalledProcessError as ex:
            msg = "Command '{}' failed: {}".format(cmd, ex)
            ecode = ex.returncode
            log.step_info(msg)
        finally:
            log.step_info()

        os.chdir(self.cwd)
        return ecode
