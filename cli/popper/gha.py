from __future__ import unicode_literals
import os
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
    def download_actions(wf, dry_run, skip_clone):
        """Clone actions that reference a repository."""
        cloned = set()
        infoed = False
        actions_cache_path = os.path.join('/', 'tmp', 'actions')

        for _, a in wf.action.items():
            if ('docker://' in a['uses']
                    or './' in a['uses'] or a['uses'] == 'sh'):
                continue

            url, service, user, repo, action_dir, version = scm.parse(
                a['uses'])

            repo_dir = os.path.join(
                actions_cache_path, service, user, repo
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
    def instantiate_runners(runtime, wf, workspace, env,
                            dry_run, skip_pull):
        """Factory of ActionRunner instances, one for each action.

        Note:
            If the `uses` attribute startswith a './' and does not have
            a `Dockerfile` in the referenced directory, we assume that
            it is meant to be run on the Host machine and ignore the
            runtime argument.
            Same is the case when the `uses` attribute is equal to 'sh'.
        """
        for _, a in wf.action.items():

            if a['uses'] == 'sh':
                a['runner'] = HostRunner(a, workspace, env, dry_run, skip_pull)
                continue

            if a['uses'].startswith('./'):
                if not os.path.isfile(
                    os.path.join(scm.get_git_root_folder(), a['uses'],
                                 'Dockerfile')):

                    a['runner'] = HostRunner(
                        a, workspace, env, dry_run, skip_pull)
                    continue

            if runtime == 'docker':
                a['runner'] = DockerRunner(
                    a, workspace, env, dry_run, skip_pull)

            elif runtime == 'singularity':
                a['runner'] = SingularityRunner(
                    a, workspace, env, dry_run, skip_pull)

    def run(self, action, skip_clone, skip_pull, skip, workspace,
            reuse, dry_run, parallel, with_dependencies, runtime,
            skip_secrets_prompt=False):
        """Run the workflow or a specific action."""
        if scm.get_user():
            repo_id = '{}/{}'.format(scm.get_user(), scm.get_name())
        else:
            repo_id = 'unknown'

        new_wf = deepcopy(self.wf)

        if skip:
            new_wf = Workflow.skip_actions(self.wf, skip)

        if action:
            new_wf = Workflow.filter_action(self.wf, action, with_dependencies)

        new_wf.check_for_unreachable_actions(skip)

        env = {
            'HOME': os.environ['HOME'],
            'GITHUB_WORKFLOW': new_wf.name,
            'GITHUB_ACTION': '',
            'GITHUB_ACTOR': 'popper',
            'GITHUB_REPOSITORY': repo_id,
            'GITHUB_EVENT_NAME': new_wf.on,
            'GITHUB_EVENT_PATH': '/tmp/github_event.json',
            'GITHUB_WORKSPACE': workspace,
            'GITHUB_SHA': scm.get_sha(),
            'GITHUB_REF': scm.get_ref()
        }

        for e in dict(env):
            env.update({e.replace('GITHUB_', 'POPPER_'): env[e]})

        WorkflowRunner.check_secrets(new_wf, dry_run, skip_secrets_prompt)
        WorkflowRunner.download_actions(new_wf, dry_run, skip_clone)
        WorkflowRunner.instantiate_runners(
            runtime, new_wf, workspace, env, dry_run, skip_pull)

        for s in new_wf.get_stages():
            WorkflowRunner.run_stage(new_wf, s, reuse, parallel)

    @staticmethod
    def run_stage(wf, stage, reuse=False, parallel=False):
        if parallel:
            with ProcessPoolExecutor(max_workers=mp.cpu_count()) as ex:
                flist = {
                    ex.submit(wf.action[a]['runner'].run, reuse):
                        a for a in stage
                }
                popper.cli.flist = flist
                for future in as_completed(flist):
                    future.result()
                    log.info('Action ran successfully !')
        else:
            for a in stage:
                wf.action[a]['runner'].run(reuse)


class ActionRunner(object):
    """An action runner.
    """

    def __init__(self, action, workspace, env, dry_run, skip_pull):
        self.action = action
        self.workspace = workspace
        self.env = dict(env)
        self.dry_run = dry_run
        self.skip_pull = skip_pull
        self.msg_prefix = "DRYRUN: " if dry_run else ""

        if not os.path.exists(self.workspace):
            os.makedirs(self.workspace)

        if not os.path.exists(env['GITHUB_EVENT_PATH']):
            f = open(env['GITHUB_EVENT_PATH'], 'w')
            f.close()

    def prepare_environment(self, set_env=False):
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
        env = self.prepare_environment()
        env.pop('HOME')
        for k, v in env.items():
            os.environ.pop(k)

    def run(self, reuse=False):
        raise NotImplementedError(
            "This method is required to be implemented in derived classes."
        )


class DockerRunner(ActionRunner):
    """Runs a Github Action in Docker runtime.
    """

    def __init__(self, action, workspace, env, dry, skip_pull):
        super(DockerRunner, self).__init__(
            action, workspace, env, dry, skip_pull)
        self.cid = pu.sanitized_name(self.action['name'])
        self.container = None
        if not find_executable('docker'):
            log.fail(
                'Could not find the docker command.'
            )

    def run(self, reuse=False):
        build = True

        if 'docker://' in self.action['uses']:
            tag = self.action['uses'].replace('docker://', '')
            if ':' not in tag:
                tag += ":latest"
            build = False
            dockerfile_path = 'n/a'
        elif './' in self.action['uses']:
            action_dir = os.path.basename(
                self.action['uses'].replace('./', ''))

            if self.env['GITHUB_REPOSITORY'] == 'unknown':
                repo_id = ''
            else:
                repo_id = self.env['GITHUB_REPOSITORY']

                if action_dir:
                    repo_id += '/'

            tag = repo_id + action_dir + ':' + self.env['GITHUB_SHA']

            dockerfile_path = os.path.join(
                scm.get_git_root_folder(), self.action['uses'])
        else:
            _, _, user, repo, _, version = scm.parse(self.action['uses'])
            tag = '{}/{}:{}'.format(user, repo, version)
            dockerfile_path = os.path.join(self.action['repo_dir'],
                                           self.action['action_dir'])
        log.debug('docker tag: {}'.format(tag))
        log.debug('dockerfile path: {}'.format(dockerfile_path))

        if not reuse:
            if self.docker_exists():
                self.docker_rm()
            if build:
                self.docker_build(tag, dockerfile_path)
            else:
                self.docker_pull(tag)
            self.docker_create(tag)
        else:
            if not self.docker_exists():
                if build:
                    self.docker_build(tag, dockerfile_path)
                else:
                    self.docker_pull(tag)
                self.docker_create(tag)
            else:
                self.container.commit(self.cid, 'reuse')
                self.docker_rm()
                self.docker_create('{}:reuse'.format(self.cid))

        if self.container is not None:
            popper.cli.docker_list.append(self.container)
        e = self.docker_start()

        if e != 0:
            log.fail("Action '{}' failed!".format(self.action['name']))

    def docker_exists(self):
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
        if self.dry_run:
            return True
        images = docker_client.images.list(all=True)
        filtered_images = [i for i in images if img in i.tags]
        return filtered_images

    def docker_rm(self):
        if self.dry_run:
            return
        self.container.remove(force=True)

    def docker_create(self, img):
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

        log.debug(
            'Invoking docker_create() method\n' +
            '  img: {}\n'.format(img) +
            '  cmd: {}\n'.format(self.action.get('args', None)) +
            '  vol: {}\n'.format(volumes) +
            '  args: {}'.format(self.action.get('args', None))
        )

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

    def docker_build(self, tag, path):
        log.info('{}[{}] docker build -t {} {}'.format(
            self.msg_prefix, self.action['name'], tag, path))
        if self.dry_run:
            return
        docker_client.images.build(path=path, tag=tag, rm=True, pull=True)


class SingularityRunner(ActionRunner):
    """Runs a Github Action in Singularity runtime.
    """

    def __init__(self, action, workspace, env, dry_run, skip_pull):
        super(SingularityRunner, self).__init__(action, workspace, env,
                                                dry_run, skip_pull)
        self.cid = pu.sanitized_name(self.action['name'])
        if not find_executable('singularity'):
            log.fail(
                'Could not find the singularity command.'
            )
        s_client.quiet = True

    def run(self, reuse=False):
        """Run the action.
        """
        if reuse:
            log.fail('Reusing containers in singularity runtime is '
                     'currently not supported.')

        build = True
        if 'docker://' in self.action['uses']:
            image = self.action['uses']
            build = False

        elif './' in self.action['uses']:
            image = 'action/' + os.path.basename(self.action['uses'])
            build_path = os.path.join(
                scm.get_git_root_folder(), self.action['uses'])

        else:
            image = '/'.join(self.action['uses'].split('/')[:2])
            build_path = os.path.join(
                self.action['repo_dir'], self.action['action_dir'])

        container = self.cid + '.sif'

        if self.singularity_exists(container) and not self.skip_pull:
            self.singularity_rm(container)
        if build:
            self.singularity_build_from_recipe(build_path, container)
        else:
            self.singularity_build_from_image(image, container)

        e = self.singularity_start(container)

        if e != 0:
            log.fail('Action {} failed!'.format(self.action['name']))

    @staticmethod
    def convert(dockerfile, singularityfile):
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
    def get_reciple_file(build_path, container):
        dockerfile = os.path.join(build_path, 'Dockerfile')
        singularityfile = os.path.join(
            build_path, 'Singularity.{}'.format(container[:-4]))

        if os.path.isfile(dockerfile):
            return SingularityRunner.convert(dockerfile, singularityfile)
        else:
            log.fail('No Dockerfile was found.')

    @staticmethod
    def build_from_recipe(build_path, container):
        pwd = os.getcwd()
        os.chdir(build_path)
        recipefile = SingularityRunner.get_reciple_file(build_path, container)
        s_client.build(recipe=recipefile, image=container, build_folder=pwd)
        os.chdir(pwd)

    def singularity_exists(self, container):
        """Check whether the container exists or not.
        """
        if self.dry_run:
            return
        return os.path.exists(container)

    def singularity_rm(self, container):
        """Removes the container.
        """
        if self.dry_run:
            return
        os.remove(container)

    def singularity_build_from_image(self, image, container):
        """Build container from Docker image.
        """
        if not self.skip_pull:
            log.info('{}[{}] singularity pull {} {}'.format(
                self.msg_prefix, self.action['name'], container, image)
            )
            if not self.dry_run:
                s_client.pull(image=image, name=container)
        else:
            if not self.singularity_exists(container):
                log.fail(
                    'The required singularity container \'{}\' was not found '
                    'locally.'.format(container))

    def singularity_build_from_recipe(self, build_path, container):
        """Build container from recipefile.
        """
        filename = 'Singularity.{}'.format(container[:-4])
        log.info('{}[{}] singularity build {} {}'.format(
            self.msg_prefix, self.action['name'],
            container, os.path.join(build_path, filename))
        )
        if not self.dry_run:
            SingularityRunner.build_from_recipe(build_path, container)

    def singularity_start(self, container):
        """Starts the container to execute commands or run the runscript
        with the supplied args inside the container.
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
                container, runs)
            commands = runs
            start = s_client.execute
        else:
            info = '{}[{}] singularity run {} {}'.format(
                self.msg_prefix, self.action['name'],
                container, args)
            commands = args
            start = s_client.run

        log.info(info)
        if not self.dry_run:
            output = start(container, commands, bind=volumes,
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

    def __init__(self, action, workspace, env, dry, skip_pull):
        super(HostRunner, self).__init__(
            action, workspace, env, dry, skip_pull)
        self.cwd = os.getcwd()

    def run(self, reuse=False):
        if reuse:
            log.fail('--reuse flag is not supported for actions running '
                     'on the host.')

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

        self.prepare_environment(set_env=True)

        log.info('{}[{}] {}'.format(self.msg_prefix, self.action['name'],
                                    ' '.join(cmd)))

        if self.dry_run:
            return

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

        self.remove_environment()
        os.chdir(self.cwd)

        if ecode != 0:
            log.fail("Action '{}' failed.".format(self.action['name']))
