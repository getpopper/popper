from __future__ import unicode_literals
from builtins import dict, str, input
from concurrent.futures import ThreadPoolExecutor, as_completed
import multiprocessing as mp
import hcl
import os
import shutil
import docker
import sys
import popper.scm as scm
import popper.utils as pu
from spython.main import Client
import sys
import popper.cli
from distutils.dir_util import copy_tree


class Workflow(object):
    """A GHA workflow.
    """

    def __init__(self, wfile, workspace, quiet, debug, dry_run,
                 reuse, parallel):
        wfile = pu.find_default_wfile(wfile)

        with open(wfile, 'r') as fp:
            self.wf = hcl.load(fp)

        self.workspace = workspace
        self.debug = debug
        if debug:
            self.quiet = False
        else:
            self.quiet = quiet
        self.dry_run = dry_run
        self.reuse = reuse
        self.parallel = parallel

        self.actions_cache_path = os.path.join('/', 'tmp', 'actions')
        self.validate_syntax()
        self.check_secrets()
        self.normalize()
        self.complete_graph()

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
            'GITHUB_SHA': scm.get_sha(debug),
            'GITHUB_REF': scm.get_ref()
        }

        for e in dict(self.env):
            self.env.update({e.replace('GITHUB_', 'POPPER_'): self.env[e]})

    def validate_syntax(self):
        """ Validates the .workflow file.
        """
        resolves_present = False
        uses_present = False
        if not self.wf.get('workflow', None):
            pu.fail('A workflow block must be present\n')
        else:
            for _, wf_block in dict(self.wf['workflow']).items():
                if wf_block.get('resolves', None):
                    resolves_present = True
            if not resolves_present:
                pu.fail('[resolves] attribute must be present\n')
        if not self.wf.get('action', None):
            pu.fail('Atleast one action block must be present\n')
        else:
            for _, a_block in self.wf['action'].items():
                if a_block.get('uses', None):
                    uses_present = True
            if not uses_present:
                pu.fail('[uses] attribute must be present\n')

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
            pu.fail('[resolves] must be a list of strings or a string\n')
        if not isinstance(self.wf['on'], basestring):
            pu.fail('[on] attribute must be a string\n')
        for _, a_block in self.wf['action'].items():
            if not isinstance(a_block['uses'], basestring):
                pu.fail('[uses] attribute must be a string\n')
            if a_block.get('needs', None):
                if isinstance(a_block['needs'], basestring):
                    a_block['needs'] = [a_block['needs']]
                elif not self.is_list_of_strings(a_block['needs']):
                    pu.fail(
                        '[needs] attribute must be a list of strings \
                        or a string\n')
            if a_block.get('runs', None):
                if isinstance(a_block['runs'], basestring):
                    a_block['runs'] = [a_block['runs']]
                elif not self.is_list_of_strings(a_block['runs']):
                    pu.fail(
                        '[runs] attribute must be a list of strings \
                        or a string\n')
            if a_block.get('args', None):
                if isinstance(a_block['args'], basestring):
                    a_block['args'] = a_block['args'].split()
                elif not self.is_list_of_strings(a_block['args']):
                    pu.fail(
                        '[args] attribute must be a list of strings \
                        or a string\n')
            if a_block.get('env', None):
                if not isinstance(a_block['env'], dict):
                    pu.fail('[env] attribute must be a dict\n')
            if a_block.get('secrets', None):
                if not self.is_list_of_strings(a_block['secrets']):
                    pu.fail('[secrets] attribute must be a list of strings\n')

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
                        pu.fail('Secret {} not defined\n.'.format(s))
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
                    pu.info('[popper] cloning actions from repositories\n')
                    infoed = True

                scm.clone(url, user, repo, repo_parent_dir, version,
                          debug=self.debug)

                cloned.add('{}/{}'.format(user, repo))

    def instantiate_runners(self):
        """Factory of ActionRunner instances, one for each action"""
        for _, a in self.wf['action'].items():
            if 'docker://' in a['uses']:
                a['runner'] = DockerRunner(
                    docker.from_env(), a, self.workspace, self.env,
                    self.quiet, self.debug, self.dry_run)
                continue

            if 'shub://' in a['uses']:
                a['runner'] = SingularityRunner(
                    a, self.workspace, self.env,
                    self.quiet, self.debug, self.dry_run)
                continue

            if './' in a['uses']:
                if os.path.exists(os.path.join(a['uses'], 'Dockerfile')):
                    a['runner'] = DockerRunner(
                        docker.from_env(), a, self.workspace, self.env,
                        self.quiet, self.debug, self.dry_run)
                elif os.path.exists(os.path.join(a['uses'],
                                                 'singularity.def')):
                    a['runner'] = SingularityRunner(
                        a, self.workspace, self.env,
                        self.quiet, self.debug, self.dry_run)
                else:
                    a['runner'] = HostRunner(
                        a, self.workspace, self.env,
                        self.quiet, self.debug, self.dry_run)
                continue

            dockerfile_path = os.path.join(a['repo_dir'], a['action_dir'],
                                           'Dockerfile')
            singularityfile_path = os.path.join(a['repo_dir'], a['action_dir'],
                                                'singularity.def')

            if os.path.exists(dockerfile_path):
                a['runner'] = DockerRunner(
		    docker.from_env(), a, self.workspace, self.env,
                    self.quiet, self.debug, self.dry_run)
            elif os.path.exists(singularityfile_path):
                a['runner'] = SingularityRunner(
                    a, self.workspace, self.env,
                    self.quiet, self.debug, self.dry_run)
            else:
                a['runner'] = HostRunner(
                    a, self.workspace, self.env,
                    self.quiet, self.debug, self.dry_run)

    def run(self, action_name=None, reuse=False, parallel=False):
        """Run the pipeline or a specific action"""
        os.environ['WORKSPACE'] = self.workspace

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
                    pu.info('Action ran successfully !\n')
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
            pu.fail(
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
                pu.fail("Unable to find a .workflow file")
        elif len(parts) >= 4:
            path_to_workflow = os.path.join(
                cloned_project_dir, '/'.join(parts[3:])).split("@")[0]
            if not os.path.basename(path_to_workflow).endswith('.workflow'):
                path_to_workflow = os.path.join(
                    path_to_workflow, 'main.workflow')
            if not os.path.isfile(path_to_workflow):
                pu.fail("Unable to find a .workflow file")

        shutil.copy(path_to_workflow, project_root)
        pu.info("Successfully imported from {}\n".format(path_to_workflow))

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
            pu.info("Copied {} to {}...\n".format(os.path.join(
                cloned_project_dir, a), project_root))


class ActionRunner(object):
    """An action runner.
    """

    def __init__(self, action, workspace, env, quiet, debug, dry_run):
        self.action = action
        self.workspace = workspace
        self.env = env
        self.quiet = quiet
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
    def __init__(self, docker_client, action, workspace, env, q, d, dry):
        super(DockerRunner, self).__init__(action, workspace, env, q, d, dry)
        self.cid = self.action['name'].replace(' ', '_')
        self.docker_client = docker_client

    def run(self, reuse):
        popper.cli.docker_list.append(self.cid)
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

        e = self.docker_start()

        if e != 0:
            pu.fail('Action {} failed!\n'.format(self.action['name']))

    def docker_exists(self):
        if self.dry_run:
            return True
        container = self.docker_client.containers.list(
            all=True, filters={'name': self.cid})

        container = [c for c in container if c.name == self.cid]
        if container:
            self.container = container[0]
            return True

        return False

    def docker_rm(self):
        if self.dry_run:
            return
        self.container.remove(force=True)

    def docker_create(self, img):
        pu.info('{}[{}] docker create {} {}\n'.format(
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
        self.container = self.docker_client.containers.create(
            image=img, command=self.action.get('args', None),
            name=self.cid, volumes={v: {'bind': v} for v in volumes},
            working_dir=self.workspace, environment=env_vars,
            entrypoint=self.action.get('runs', None))


    def docker_start(self):
        pu.info('{}[{}] docker start \n'.format(self.msg_prefix,
                                                self.action['name']))
        if self.dry_run:
            return 0
        self.container.start()
        eout = self.container.logs(stream=True, stdout=True)
        err = self.container.logs(stream=True, stderr=True)
        outf = open(self.log_filename + '.out', 'wb')
        errf = open(self.log_filename + '.err', 'wb')
        for line in eout:
            outf.write(line)
        outf.close()
        for line in err:
            errf.write(line)
        errf.close()
        statuscode = self.container.wait()
        return statuscode['StatusCode']

    def docker_pull(self, img):
        pu.info('{}[{}] docker pull {}\n'.format(self.msg_prefix,
                                                 self.action['name'], img))
        if self.dry_run:
            return
        self.docker_client.images.pull(repository=img)

    def docker_build(self, tag, path):
        pu.info('{}[{}] docker build -t {} {}\n'.format(
            self.msg_prefix, self.action['name'], tag, path))
        if self.dry_run:
            return
        self.docker_client.images.build(path=path, tag=tag, rm=True, pull=True)


class SingularityRunner(ActionRunner):
    """Singularity Action Runner Class
    """

    def __init__(self, action, workspace, env, q, d, dry):
        super(SingularityRunner, self).__init__(action, workspace, env,
                                                q, d, dry)
        self.pid = self.action['name'].replace(' ', '_')
        Client.quiet = q

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

        if not reuse:
            if self.singularity_exists():
                self.singularity_rm()
            if build:
                self.singularity_build(singularityfile_path, image)
            else:
                self.singularity_pull(image)
        else:
            if not self.singularity_exists():
                if build:
                    self.singularity_build(singularityfile_path, image)
                else:
                    self.singularity_pull(image)

        e = self.singularity_start(image)

        if e != 0:
            pu.fail('Action {} failed!\n'.format(self.action['name']))

    def generate_image_name(self, image):
        """Generates the image name from the image url.
        """
        return image.replace('shub://', '').replace('/', '-') + '.simg'

    def singularity_exists(self):
        """Check whether an instance exists or not.
        """
        instances = Client.instances(quiet=self.quiet)
        for instance in instances:
            if self.pid in instance.name:
                return True
        return False

    def singularity_rm(self):
        """Stops and removes an instance.
        """
        Client.instances(self.pid, quiet=self.quiet).stop()

    def singularity_pull(self, image):
        """Pulls an docker or singularity images from hub.
        """
        Client.pull(image)

    def singularity_build(self, path, image):
        """Builds an image from a recipefile.
        """
        Client.build(os.path.join(
            path, 'singularity.def'
        ), self.generate_image_name(image))

    def singularity_start(self, image):
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
            Client.setenv(k, v)

        e = Client.run(image=self.generate_image_name(image),
                       args=' '.join(self.action.get('args', '')),
                       return_result=True)
        return e['return_code']


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

        pu.info('{}[{}] {}\n'.format(self.msg_prefix, self.action['name'],
                                     ' '.join(cmd)))

        _, ecode = pu.exec_cmd(
            ' '.join(cmd), verbose=(not self.quiet), debug=self.debug,
            ignore_error=True, log_file=self.log_filename,
            dry_run=self.dry_run, add_to_process_list=True)

        for i in self.action.get('env', {}):
            os.environ.pop(i)

        os.chdir(cwd)

        if ecode != 0:
            pu.fail("\n\nAction '{}' failed.\n.".format(self.action['name']))
