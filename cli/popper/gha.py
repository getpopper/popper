from __future__ import unicode_literals
import os
import shutil
import getpass
import subprocess
import multiprocessing as mp
from copy import deepcopy
from builtins import dict, input
from distutils.dir_util import copy_tree
from distutils.spawn import find_executable
from concurrent.futures import ThreadPoolExecutor, as_completed
from subprocess import CalledProcessError, PIPE, Popen, STDOUT

import yaml
import docker
from spython.main import Client as sclient

import popper.cli
from popper.cli import log
from popper.parser import Workflow
from popper import scm, utils as pu


yaml.Dumper.ignore_aliases = lambda *args: True


class WorkflowRunner(object):
    """A GHA workflow runner.
    """

    def __init__(self, workflow):

        self.actions_cache_path = os.path.join('/', 'tmp', 'actions')
        self.wf = workflow
        log.debug('workflow:\n{}'.format(
            yaml.dump(self.wf, default_flow_style=False, default_style='')))

    def check_secrets(self, wf, dry_run, skip_secrets_prompt):
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
        for _, a in wf.actions.items():
            for s in a.get('secrets', []):
                if s not in os.environ:
                    if os.environ.get('CI') == 'true':
                        log.fail('Secret {} not defined'.format(s))
                    else:
                        val = getpass.getpass(
                            'Enter the value for {} : '.format(s))
                        os.environ[s] = val

    def download_actions(self, wf, dry_run, skip_clone):
        """Clone actions that reference a repository."""
        cloned = set()
        infoed = False

        for _, a in wf.actions.items():
            if ('docker://' in a['uses'] or 'shub://' in a['uses'] or
                    './' in a['uses'] or a['uses'] == 'sh'):
                continue

            url, service, usr, repo, action_dir, version = scm.parse(a['uses'])

            repo_dir = os.path.join(
                self.actions_cache_path, service, usr, repo
            )

            a['repo_dir'] = repo_dir
            a['action_dir'] = action_dir

            if dry_run:
                continue

            if skip_clone:
                if not os.path.exists(repo_dir):
                    log.fail('Cannot find action folder locally.')
                continue

            if not infoed:
                log.info('[popper] cloning action repositories')
                infoed = True

            if '{}/{}'.format(usr, repo) in cloned:
                continue

            log.info('[popper] - {}/{}/{}@{}'.format(url, usr, repo, version))
            scm.clone(url, usr, repo, repo_dir, version)
            cloned.add('{}/{}'.format(usr, repo))

    def instantiate_runners(self, wf, workspace, env, dry_run, skip_pull):
        """Factory of ActionRunner instances, one for each action"""
        for _, a in wf.actions.items():
            if a['uses'] == 'sh':
                a['runner'] = HostRunner(
                    a, workspace, env,
                    dry_run, skip_pull)
                continue

            if 'docker://' in a['uses']:
                a['runner'] = DockerRunner(
                    a, workspace, env,
                    dry_run, skip_pull)
                continue

            if 'shub://' in a['uses']:
                a['runner'] = SingularityRunner(
                    a, workspace, env,
                    dry_run, skip_pull)
                continue

            if './' in a['uses']:
                if os.path.exists(os.path.join(a['uses'], 'Dockerfile')):
                    a['runner'] = DockerRunner(
                        a, workspace, env,
                        dry_run, skip_pull)
                elif os.path.exists(os.path.join(a['uses'],
                                                 'Singularity')):
                    a['runner'] = SingularityRunner(
                        a, workspace, env,
                        dry_run, skip_pull)
                else:
                    a['runner'] = HostRunner(
                        a, workspace, env,
                        dry_run, skip_pull)
                continue

            dockerfile_path = os.path.join(a['repo_dir'], a['action_dir'],
                                           'Dockerfile')
            singularityfile_path = os.path.join(a['repo_dir'], a['action_dir'],
                                                'Singularity')

            if os.path.exists(dockerfile_path):
                a['runner'] = DockerRunner(
                    a, workspace, env,
                    dry_run, skip_pull)
            elif os.path.exists(singularityfile_path):
                a['runner'] = SingularityRunner(
                    a, workspace, env,
                    dry_run, skip_pull)
            else:
                a['runner'] = HostRunner(
                    a, workspace, env,
                    dry_run, skip_pull)

    def run(self, action, skip_clone, skip_pull, skip, workspace,
            reuse, dry_run, parallel, with_dependencies,
            skip_secrets_prompt=False):
        """Run the pipeline or a specific action"""
        os.environ['WORKSPACE'] = workspace

        if scm.get_user():
            repo_id = '{}/{}'.format(scm.get_user(), scm.get_name())
        else:
            repo_id = 'unknown'

        if with_dependencies and (not action):
            log.fail('`--with-dependencies` can be used only with '
                     'action argument.')

        if skip and action:
            log.fail('`--skip` can\'t be used when action argument '
                     'is passed.')

        new_wf = deepcopy(self.wf)

        if skip:
            new_wf = self.wf.skip_actions(skip)

        if action:
            new_wf = self.wf.filter_action(action, with_dependencies)

        new_wf.check_for_unreachable_actions(skip)

        env = {
            'GITHUB_WORKSPACE': workspace,
            'GITHUB_WORKFLOW': new_wf.name,
            'GITHUB_ACTOR': 'popper',
            'GITHUB_REPOSITORY': repo_id,
            'GITHUB_EVENT_NAME': new_wf.on,
            'GITHUB_EVENT_PATH': '/tmp/github_event.json',
            'GITHUB_SHA': scm.get_sha(),
            'GITHUB_REF': scm.get_ref()
        }

        for e in dict(env):
            env.update({e.replace('GITHUB_', 'POPPER_'): env[e]})

        self.check_secrets(new_wf, dry_run, skip_secrets_prompt)
        self.download_actions(new_wf, dry_run, skip_clone)
        self.instantiate_runners(new_wf, workspace, env, dry_run, skip_pull)

        for s in new_wf.get_stages():
            self.run_stage(new_wf, s, reuse, parallel)

    def run_stage(self, wf, stage, reuse=False, parallel=False):
        if parallel:
            with ThreadPoolExecutor(max_workers=mp.cpu_count()) as ex:
                flist = {
                    ex.submit(wf.get_runner(a).run, reuse):
                        a for a in stage
                }
                popper.cli.flist = flist
                for future in as_completed(flist):
                    future.result()
                    log.info('Action ran successfully !')
        else:
            for action in stage:
                wf.get_runner(action).run(reuse)

    @staticmethod
    def import_from_repo(action_ref, project_root):
        url, service, user, repo, action_dir, version = scm.parse(action_ref)

        cloned_project_dir = os.path.join("/tmp", service, user, repo)

        scm.clone(url, user, repo, cloned_project_dir, version)

        if not action_dir:
            ptw_one = os.path.join(cloned_project_dir, "main.workflow")
            ptw_two = os.path.join(cloned_project_dir, ".github/main.workflow")
            if os.path.isfile(ptw_one):
                path_to_workflow = ptw_one
            elif os.path.isfile(ptw_two):
                path_to_workflow = ptw_two
            else:
                log.fail("Unable to find main.workflow file")
        else:
            path_to_workflow = os.path.join(
                cloned_project_dir, action_dir)
            if not os.path.basename(path_to_workflow).endswith('.workflow'):
                path_to_workflow = os.path.join(
                    path_to_workflow, 'main.workflow')
            if not os.path.isfile(path_to_workflow):
                log.fail("Unable to find a main.workflow file")

        if '.github/' in path_to_workflow:
            path_to_copy = os.path.dirname(os.path.dirname(path_to_workflow))
        else:
            path_to_copy = os.path.dirname(path_to_workflow)

        copy_tree(path_to_copy, project_root)
        log.info("Successfully imported from {}".format(action_ref))


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

    def run(self, reuse=False):
        raise NotImplementedError(
            "This method is required to be implemented in derived classes."
        )


class DockerRunner(ActionRunner):
    def __init__(self, action, workspace, env, dry, skip_pull):
        super(DockerRunner, self).__init__(
            action, workspace, env, dry, skip_pull)
        self.cid = self.action['name'].replace(' ', '_')
        self.docker_client = docker.from_env()
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

            dockerfile_path = os.path.join(os.getcwd(), self.action['uses'])
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

        if self.container is not None:
            popper.cli.docker_list.append(self.container)
        e = self.docker_start()

        if e != 0:
            log.fail("Action '{}' failed!".format(self.action['name']))

    def docker_exists(self):
        if self.dry_run:
            return True
        containers = self.docker_client.containers.list(
            all=True, filters={'name': self.cid})

        filtered_containers = [c for c in containers if c.name == self.cid]
        if len(filtered_containers):
            self.container = filtered_containers[0]
            return True

        return False

    def docker_image_exists(self, img):
        if self.dry_run:
            return True
        images = self.docker_client.images.list(all=True)
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
        env_vars = self.action.get('env', {})

        for s in self.action.get('secrets', []):
            env_vars.update({s: os.environ.get(s)})

        for e, v in self.env.items():
            env_vars.update({e: v})
        env_vars.update({'HOME': os.environ['HOME']})

        # Bind the local volumes to volumes inside container
        volumes = {}
        volumes[env_vars['HOME']] = {'bind': env_vars['HOME']}
        volumes[env_vars['GITHUB_EVENT_PATH']] = {
            'bind': '/github/workflow/event.json'}
        volumes[env_vars['GITHUB_WORKSPACE']] = {
            'bind': env_vars['GITHUB_WORKSPACE']}
        volumes['/var/run/docker.sock'] = {'bind': '/var/run/docker.sock'}

        # Update the corresponding env vars accordingly.
        env_vars['GITHUB_EVENT_PATH'] = '/github/workflow/event.json'

        log.debug(
            'Invoking docker_create() method\n' +
            '  img: {}\n'.format(img) +
            '  cmd: {}\n'.format(self.action.get('args', None)) +
            '  vol: {}\n'.format(volumes) +
            '  args: {}'.format(self.action.get('args', None))
        )

        self.container = self.docker_client.containers.create(
            image=img,
            command=self.action.get('args', None),
            name=self.cid,
            volumes=volumes,
            working_dir=env_vars['GITHUB_WORKSPACE'],
            environment=env_vars,
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
            self.docker_client.images.pull(repository=img)
        else:
            if not self.docker_image_exists(img):
                log.fail('The required docker image {} was not found locally.'
                         .format(img))

    def docker_build(self, tag, path):
        log.info('{}[{}] docker build -t {} {}'.format(
            self.msg_prefix, self.action['name'], tag, path))
        if self.dry_run:
            return
        self.docker_client.images.build(path=path, tag=tag, rm=True, pull=True)


class SingularityRunner(ActionRunner):
    """Singularity Action Runner Class
    """

    def __init__(self, action, workspace, env, dry, skip_pull):
        super(SingularityRunner, self).__init__(action, workspace, env,
                                                dry, skip_pull)
        self.pid = self.action['name'].replace(' ', '_')
        if not find_executable('singularity'):
            log.fail(
                'Could not find the singularity command.'
            )

    def run(self, reuse=False):
        """Runs the singularity action
        """
        build = True
        if 'shub://' in self.action['uses']:
            image = self.action['uses']
            build = False
        elif './' in self.action['uses']:
            image = 'action/' + os.path.basename(self.action['uses'])
            singularityfile_path = os.path.join(
                os.getcwd(), self.action['uses'])
        else:
            image = '/'.join(self.action['uses'].split('/')[:2])
            singularityfile_path = os.path.join(self.action['repo_dir'],
                                                self.action['action_dir'])
        self.image_name = self.pid + '.simg'
        if (not reuse) and (not self.skip_pull):
            if self.singularity_exists():
                self.singularity_rm()
            if build:
                self.singularity_build(singularityfile_path)
            else:
                self.singularity_pull(image)
        else:
            if not self.singularity_exists():
                if build:
                    self.singularity_build(singularityfile_path)
                else:
                    self.singularity_pull(image)

        e = self.singularity_start()

        if e != 0:
            log.fail('Action {} failed!'.format(self.action['name']))

    def singularity_exists(self):
        """Check whether an instance exists or not.
        """
        if os.path.exists(self.image_name):
            return True
        return False

    def singularity_rm(self):
        """Stops and removes an instance.
        """
        os.remove(self.image_name)

    def singularity_pull(self, image):
        """Pulls an docker or singularity images from hub.
        """
        if not self.skip_pull:
            log.info('{}[{}] singularity pull {}'.format(
                self.msg_prefix, self.action['name'], image)
            )
            if not self.dry_run:
                sclient.pull(image, name=self.image_name)
        else:
            if not self.singularity_exists():
                log.fail('The required singularity image {} was not found '
                         'locally.'.format(self.image_name))

    def singularity_build(self, path):
        """Builds an image from a recipefile.
        """
        recipefile_path = os.path.join(path, 'Singularity')
        log.info('{}[{}] singularity build {} {}'.format(
            self.msg_prefix, self.action['name'],
            self.image_name, recipefile_path)
        )
        if not self.dry_run:
            sclient.build(recipefile_path, self.image_name)

    def singularity_start(self):
        """Starts a singularity instance based on the image.
        """
        env_vars = self.action.get('env', {})

        for s in self.action.get('secrets', []):
            env_vars.update({s: os.environ[s]})

        for e, v in self.env.items():
            env_vars.update({e: v})

        env_vars.update({'HOME': os.environ['HOME']})

        # sets the env variables
        for k, v in env_vars.items():
            sclient.setenv(k, v)
        args = self.action.get('args', None)
        runs = self.action.get('runs', None)

        ecode = None
        bind_list = [self.workspace, os.environ['HOME']]

        if runs:
            info = '{}[{}] singularity exec {} {}'.format(
                self.msg_prefix, self.action['name'],
                self.image_name, runs)
            commands = runs
            start = sclient.execute
        else:
            info = '{}[{}] singularity run {} {}'.format(
                self.msg_prefix, self.action['name'],
                self.image_name, args)
            commands = args
            start = sclient.run

        log.info(info)
        if not self.dry_run:
            output = start(self.image_name, commands, contain=True,
                           bind=bind_list, stream=True)

            try:
                for line in output:
                    log.action_info(line)
                ecode = 0
            except subprocess.CalledProcessError as ex:
                ecode = ex.returncode
        else:
            ecode = 0
        return ecode


class HostRunner(ActionRunner):
    """
    Host Action Runner Class.
    """

    def __init__(self, action, workspace, env, dry, skip_pull):
        super(HostRunner, self).__init__(
            action, workspace, env, dry, skip_pull)
        self.cwd = os.getcwd()

    def run(self, reuse=False):
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

        os.environ.update(self.action.get('env', {}))

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
                log.info(line_decoded[:-1])

            p.wait()
            ecode = p.poll()
            log.debug('Code returned by process: {}'.format(ecode))

        except CalledProcessError as ex:
            msg = "Command '{}' failed: {}".format(cmd, ex)
            ecode = ex.returncode
            log.info(msg)
        finally:
            log.info()

        # remove variables that we added to the environment
        for i in self.action.get('env', {}):
            os.environ.pop(i)

        os.chdir(self.cwd)

        if ecode != 0:
            log.fail("Action '{}' failed.".format(self.action['name']))
