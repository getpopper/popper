from __future__ import unicode_literals
import multiprocessing as mp
import os
import shutil
import subprocess
import time
from builtins import dict, input, str
from concurrent.futures import ThreadPoolExecutor, as_completed
import docker
import hcl
import popper.cli
from popper import scm, utils as pu
from spython.main import Client as sclient
from popper.cli import log
from distutils.dir_util import copy_tree


class Workflow(object):
    """A GHA workflow.
    """

    def __init__(self, wfile, workspace, debug, dry_run,
                 reuse, parallel):
        wfile = pu.find_default_wfile(wfile)

        with open(wfile, 'r') as fp:
            self.wf = hcl.load(fp)

        self.workspace = workspace
        self.debug = debug
        self.dry_run = dry_run
        self.reuse = reuse
        self.parallel = parallel

        self.actions_cache_path = os.path.join('/', 'tmp', 'actions')
        self.validate_syntax()
        self.check_secrets()
        self.normalize()
        self.complete_graph()

    def validate_syntax(self):
        """ Validates the .workflow file.
        """
        resolves_present = False
        uses_present = False
        if not self.wf.get('workflow', None):
            log.fail('A workflow block must be present')
        else:
            for _, wf_block in dict(self.wf['workflow']).items():
                if wf_block.get('resolves', None):
                    resolves_present = True
            if not resolves_present:
                log.fail('[resolves] attribute must be present')
        if not self.wf.get('action', None):
            log.fail('Atleast one action block must be present')
        else:
            for _, a_block in self.wf['action'].items():
                if a_block.get('uses', None):
                    uses_present = True
            if not uses_present:
                log.fail('[uses] attribute must be present')

    def is_list_of_strings(self, lst):
        try:
            basestring
        except UnboundLocalError:
            basestring = str
        return bool(lst) and isinstance(lst, list) and all(
            isinstance(elem, basestring) for elem in lst)

    def normalize(self):
        """normalize the dictionary representation of the workflow"""

        # modify from this:
        #
        #   "workflow": {
        #     "test-and-deploy": {
        #       "resolves": "deploy"
        #     }
        #   }
        #
        # to this:
        #
        #   "workflow": {
        #     "name": "test-and-deploy",
        #     "on": "push",
        #     "resolves": "deploy"
        #   }
        for wf_name, wf_block in dict(self.wf['workflow']).items():
            self.wf['name'] = wf_name
            self.wf['on'] = wf_block.get('on', 'push')
            self.wf['resolves'] = wf_block['resolves']

        # python 2 to 3 compatibility
        try:
            basestring
        except UnboundLocalError:
            basestring = str

        # create a list for all attributes that can be either string or list
        if isinstance(self.wf['resolves'], basestring):
            self.wf['resolves'] = [self.wf['resolves']]
        elif not self.is_list_of_strings(self.wf['resolves']):
            log.fail('[resolves] must be a list of strings or a string')
        if not isinstance(self.wf['on'], basestring):
            log.fail('[on] attribute must be a string')
        for _, a_block in self.wf['action'].items():
            if not isinstance(a_block['uses'], basestring):
                log.fail('[uses] attribute must be a string')
            if a_block.get('needs', None):
                if isinstance(a_block['needs'], basestring):
                    a_block['needs'] = [a_block['needs']]
                elif not self.is_list_of_strings(a_block['needs']):
                    log.fail(
                        '[needs] attribute must be a list of strings \
                        or a string')
            if a_block.get('runs', None):
                if isinstance(a_block['runs'], basestring):
                    a_block['runs'] = [a_block['runs']]
                elif not self.is_list_of_strings(a_block['runs']):
                    log.fail(
                        '[runs] attribute must be a list of strings \
                        or a string')
            if a_block.get('args', None):
                if isinstance(a_block['args'], basestring):
                    a_block['args'] = a_block['args'].split()
                elif not self.is_list_of_strings(a_block['args']):
                    log.fail(
                        '[args] attribute must be a list of strings \
                        or a string')
            if a_block.get('env', None):
                if not isinstance(a_block['env'], dict):
                    log.fail('[env] attribute must be a dict')
            if a_block.get('secrets', None):
                if not self.is_list_of_strings(a_block['secrets']):
                    log.fail('[secrets] attribute must be a list of strings')

    def complete_graph(self):
        """A GHA workflow is defined by specifying edges that point to the
        previous nodes they depend on. To make the workflow easier to process,
        we add forward edges. We also obtains the root nodes.
        """
        root_nodes = set()

        for name, a_block in self.wf['action'].items():

            a_block['name'] = name

            for n in a_block.get('needs', []):
                if not self.wf['action'][n].get('next', None):
                    self.wf['action'][n]['next'] = set()
                self.wf['action'][n]['next'].add(name)

            if not a_block.get('needs', None):
                root_nodes.add(name)

        self.wf['root'] = root_nodes

    def check_secrets(self):
        if self.dry_run:
            return
        for _, a in self.wf['action'].items():
            for s in a.get('secrets', []):
                if s not in os.environ:
                    if os.environ.get('CI') == "true":
                        log.fail('Secret {} not defined'.format(s))
                    else:
                        val = input("Enter the value for {0}:\n".format(s))
                        os.environ[s] = val

    def download_actions(self):
        """Clone actions that reference a repository."""
        cloned = set()
        infoed = False
        for _, a in self.wf['action'].items():
            if ('docker://' in a['uses'] or
                'shub://' in a['uses'] or
                    './' in a['uses']):
                continue

            url, service, user, repo, action, action_dir, version = pu.parse(
                a['uses'])

            repo_parent_dir = os.path.join(
                self.actions_cache_path, service, user
            )
            a['repo_dir'] = os.path.join(repo_parent_dir, repo)
            a['action_dir'] = action_dir
            if '{}/{}'.format(user, repo) in cloned:
                continue

            if not os.path.exists(repo_parent_dir):
                os.makedirs(repo_parent_dir)

            if not self.dry_run:
                if not infoed:
                    log.info('[popper] cloning actions from repositories')
                    infoed = True

                scm.clone(url, user, repo, repo_parent_dir, version,
                          debug=self.debug)

                cloned.add('{}/{}'.format(user, repo))

    def instantiate_runners(self):
        """Factory of ActionRunner instances, one for each action"""
        for _, a in self.wf['action'].items():
            if 'docker://' in a['uses']:
                a['runner'] = DockerRunner(
                    a, self.workspace, self.env,
                    self.debug, self.dry_run)
                continue

            if 'shub://' in a['uses']:
                a['runner'] = SingularityRunner(
                    a, self.workspace, self.env,
                    self.debug, self.dry_run)
                continue

            if './' in a['uses']:
                if os.path.exists(os.path.join(a['uses'], 'Dockerfile')):
                    a['runner'] = DockerRunner(
                        a, self.workspace, self.env,
                        self.debug, self.dry_run)
                elif os.path.exists(os.path.join(a['uses'],
                                                 'singularity.def')):
                    a['runner'] = SingularityRunner(
                        a, self.workspace, self.env,
                        self.debug, self.dry_run)
                else:
                    a['runner'] = HostRunner(
                        a, self.workspace, self.env,
                        self.debug, self.dry_run)
                continue

            dockerfile_path = os.path.join(a['repo_dir'], a['action_dir'],
                                           'Dockerfile')
            singularityfile_path = os.path.join(a['repo_dir'], a['action_dir'],
                                                'singularity.def')

            if os.path.exists(dockerfile_path):
                a['runner'] = DockerRunner(
                    a, self.workspace, self.env,
                    self.debug, self.dry_run)
            elif os.path.exists(singularityfile_path):
                a['runner'] = SingularityRunner(
                    a, self.workspace, self.env,
                    self.debug, self.dry_run)
            else:
                a['runner'] = HostRunner(
                    a, self.workspace, self.env,
                    self.debug, self.dry_run)

    def run(self, action_name=None, reuse=False, parallel=False):
        """Run the pipeline or a specific action"""
        os.environ['WORKSPACE'] = self.workspace

        if scm.get_user():
            repo_id = '{}/{}'.format(scm.get_user(), scm.get_name())
        else:
            repo_id = 'unknown'

        self.env = {
            'GITHUB_WORKSPACE': self.workspace,
            'GITHUB_WORKFLOW': self.wf['name'],
            'GITHUB_ACTOR': 'popper',
            'GITHUB_REPOSITORY': repo_id,
            'GITHUB_EVENT_NAME': self.wf['on'],
            'GITHUB_EVENT_PATH': '/{}/{}'.format(self.workspace,
                                                 'workflow/event.json'),
            'GITHUB_SHA': scm.get_sha(self.debug),
            'GITHUB_REF': scm.get_ref()
        }

        for e in dict(self.env):
            self.env.update({e.replace('GITHUB_', 'POPPER_'): self.env[e]})

        self.download_actions()
        self.instantiate_runners()

        if action_name:
            self.wf['action'][action_name]['runner'].run(reuse)
        else:
            for s in self.get_stages():
                self.run_stage(s, reuse, parallel)

    def run_stage(self, stage, reuse=False, parallel=False):
        if parallel:
            with ThreadPoolExecutor(max_workers=mp.cpu_count()) as ex:
                flist = {
                    ex.submit(self.wf['action'][a]['runner'].run, reuse):
                        a for a in stage
                }
                popper.cli.flist = flist
                for future in as_completed(flist):
                    future.result()
                    log.info('Action ran successfully !')
        else:
            for action in stage:
                self.wf['action'][action]['runner'].run(reuse)

    @pu.threadsafe_generator
    def get_stages(self):
        """Generator of stages. A stages is a list of actions that can be
        executed in parallel.
        """
        current_stage = self.wf['root']

        while current_stage:
            yield current_stage
            next_stage = set()
            for n in current_stage:
                next_stage.update(self.wf['action'][n].get('next', set()))
            current_stage = next_stage

    @staticmethod
    def import_from_repo(path, project_root):
        parts = pu.get_parts(path)
        if len(parts) < 3:
            log.fail(
                'Required url format: \
                 <url>/<user>/<repo>[/folder[/wf.workflow]]'
            )

        url, service, user, repo, _, _, version = pu.parse(path)
        cloned_project_dir = os.path.join("/tmp", service, user, repo)
        scm.clone(url, user, repo, os.path.dirname(
            cloned_project_dir), version
        )

        if len(parts) == 3:
            ptw_one = os.path.join(cloned_project_dir, "main.workflow")
            ptw_two = os.path.join(cloned_project_dir, ".github/main.workflow")
            if os.path.isfile(ptw_one):
                path_to_workflow = ptw_one
            elif os.path.isfile(ptw_two):
                path_to_workflow = ptw_two
            else:
                log.fail("Unable to find a .workflow file")
        elif len(parts) >= 4:
            path_to_workflow = os.path.join(
                cloned_project_dir, '/'.join(parts[3:])).split("@")[0]
            if not os.path.basename(path_to_workflow).endswith('.workflow'):
                path_to_workflow = os.path.join(
                    path_to_workflow, 'main.workflow')
            if not os.path.isfile(path_to_workflow):
                log.fail("Unable to find a .workflow file")

        shutil.copy(path_to_workflow, project_root)
        log.info("Successfully imported from {}".format(path_to_workflow))

        with open(path_to_workflow, 'r') as fp:
            wf = hcl.load(fp)

        action_paths = list()
        if wf.get('action', None):
            for _, a_block in wf['action'].items():
                if a_block['uses'].startswith("./"):
                    action_paths.append(a_block['uses'])

        action_paths = set([a.split("/")[1] for a in action_paths])
        for a in action_paths:
            copy_tree(os.path.join(cloned_project_dir, a),
                      os.path.join(project_root, a))
            log.info("Copied {} to {}...".format(os.path.join(
                cloned_project_dir, a), project_root))


class ActionRunner(object):
    """An action runner.
    """

    def __init__(self, action, workspace, env, debug, dry_run):
        self.action = action
        self.workspace = workspace
        self.env = env
        self.debug = debug
        self.dry_run = dry_run
        self.msg_prefix = "DRYRUN: " if dry_run else ""

        if not os.path.exists(self.workspace):
            os.makedirs(self.workspace)

        self.log_path = os.path.join(self.workspace, 'popper_logs')
        if not os.path.exists(self.log_path):
            os.makedirs(self.log_path)
        self.log_filename = os.path.join(
            self.log_path, self.action['name'].replace(' ', '-'))

    def run(self, reuse=False):
        raise NotImplementedError(
            "This method is required to be implemented in derived classes."
        )


class DockerRunner(ActionRunner):
    def __init__(self, action, workspace, env, q, d, dry):
        super(DockerRunner, self).__init__(action, workspace, env, q, d, dry)
        self.cid = self.action['name'].replace(' ', '_')
        self.docker_client = docker.from_env()
        self.container = None

    def run(self, reuse=False):
        build = True

        if 'docker://' in self.action['uses']:
            tag = self.action['uses'].replace('docker://', '')
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

            tag = (
                'popper/' + repo_id + action_dir + ':' + self.env['GITHUB_SHA']
            )

            dockerfile_path = os.path.join(os.getcwd(), self.action['uses'])
        else:
            tag = '/'.join(self.action['uses'].split('/')[:2])
            dockerfile_path = os.path.join(self.action['repo_dir'],
                                           self.action['action_dir'])

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
            log.fail('Action {} failed!'.format(self.action['name']))

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
        volumes = [self.workspace, os.environ['HOME'], '/var/run/docker.sock']
        log.debug('Invoking docker_create() method')
        self.container = self.docker_client.containers.create(
            image=img,
            command=self.action.get('args', None),
            name=self.cid,
            volumes={v: {'bind': v} for v in volumes},
            working_dir=self.workspace,
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
        def b(t):
            if isinstance(t, bytes):
                return t.decode('utf-8')
            return t
        cout = self.container.logs(stream=True)
        for line in cout:
            log.action_info(b(line).strip('\n'))

        return self.container.wait()['StatusCode']

    def docker_pull(self, img):
        log.info('{}[{}] docker pull {}'.format(self.msg_prefix,
                                                 self.action['name'], img))
        if self.dry_run:
            return
        self.docker_client.images.pull(repository=img)

    def docker_build(self, tag, path):
        log.info('{}[{}] docker build -t {} {}'.format(
            self.msg_prefix, self.action['name'], tag, path))
        if self.dry_run:
            return
        self.docker_client.images.build(path=path, tag=tag, rm=True, pull=True)


class SingularityRunner(ActionRunner):
    """Singularity Action Runner Class
    """

    def __init__(self, action, workspace, env, d, dry):
        super(SingularityRunner, self).__init__(action, workspace, env,
                                                d, dry)
        self.pid = self.action['name'].replace(' ', '_')
        sclient.debug = d

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
        if not reuse:
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
        log.info('{}[{}] singularity pull {}'.format(
            self.msg_prefix, self.action['name'], image)
        )
        if not self.dry_run:
            sclient.pull(image, name=self.image_name)

    def singularity_build(self, path):
        """Builds an image from a recipefile.
        """
        recipefile_path = os.path.join(path, 'singularity.def')
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

            outf = open(self.log_filename + '.out', 'w')
            errf = open(self.log_filename + '.err', 'w')
            try:
                for line in output:
                    log.info(line)
                    outf.write(line)
                ecode = 0
            except subprocess.CalledProcessError as ex:
                errf.write(ex.stderr if ex.stderr else '')
                ecode = ex.returncode
            finally:
                outf.close()
                errf.close()
        else:
            ecode = 0
        return ecode


class HostRunner(ActionRunner):
    def __init__(self, action, workspace, env, q, d, dry):
        super(HostRunner, self).__init__(action, workspace, env, q, d, dry)
        self.cwd = os.getcwd()

    def run(self, reuse=False):
        cmd = self.action.get('runs', ['entrypoint.sh'])
        cmd[0] = os.path.join('./', cmd[0])
        cmd.extend(self.action.get('args', ''))

        cwd = self.cwd
        if not self.dry_run:
            if 'repo_dir' in self.action:
                os.chdir(self.action['repo_dir'])
                cmd[0] = os.path.join(self.action['repo_dir'], cmd[0])
            else:
                os.chdir(os.path.join(cwd, self.action['uses']))
                cmd[0] = os.path.join(cwd, self.action['uses'], cmd[0])

        os.environ.update(self.action.get('env', {}))

        log.info('{}[{}] {}'.format(self.msg_prefix, self.action['name'],
                                     ' '.join(cmd)))

        _, ecode = pu.exec_cmd(
            ' '.join(cmd), verbose=True, debug=self.debug,
            ignore_error=True, log_file=self.log_filename,
            dry_run=self.dry_run, add_to_process_list=True)

        for i in self.action.get('env', {}):
            os.environ.pop(i)

        os.chdir(cwd)

        if ecode != 0:
            log.fail("Action '{}' failed.".format(self.action['name']))
