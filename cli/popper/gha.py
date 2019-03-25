from __future__ import unicode_literals
from builtins import dict, str
from concurrent.futures import ThreadPoolExecutor, as_completed
import multiprocessing as mp
import hcl
import os
import popper.utils as pu
import popper.scm as scm
from spython.main import Client


class Workflow(object):
    """A GHA workflow.
    """

    def __init__(self, wfile, workspace, quiet, debug, dry_run):
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

        self.actions_cache_path = os.path.join('/', 'tmp', 'actions')
        self.validate_syntax()
        self.check_secrets()
        self.normalize()
        self.complete_graph()

        self.env = {
            'GITHUB_WORKSPACE': self.workspace,
            'GITHUB_WORKFLOW': self.wf['name'],
            'GITHUB_ACTOR': 'popper',
            'GITHUB_REPOSITORY': '{}/{}'.format(scm.get_user(),
                                                scm.get_name()),
            'GITHUB_EVENT_NAME': self.wf['on'],
            'GITHUB_EVENT_PATH': '/{}/{}'.format(self.workspace,
                                                 'workflow/event.json'),
            'GITHUB_SHA': scm.get_sha(),
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
        for _, a in self.wf['action'].items():
            for s in a.get('secrets', []):
                if s not in os.environ:
                    pu.fail('Secret {} not defined\n.'.format(s))

    def download_actions(self):
        """Clone actions that reference a repository."""
        cloned = set()
        infoed = False
        for _, a in self.wf['action'].items():
            if 'docker://' in a['uses'] or
            'shub://' in a['uses'] or
            './' in a['uses']:
                continue

            action = None

            if a['uses'].startswith('https://'):
                a['uses'] = a['uses'][8:]
                parts = a['uses'].split('/')
                url = 'https://' + parts[0]
                service = parts[0]
                user = parts[1]
                repo = parts[2]
            elif a['uses'].startswith('http://'):
                a['uses'] = a['uses'][7:]
                parts = a['uses'].split('/')
                url = 'http://' + parts[0]
                service = parts[0]
                user = parts[1]
                repo = parts[2]
            elif a['uses'].startswith('git@'):
                url, rest = a['uses'].split(':')
                user, repo = rest.split('/')
                service = url[4:]
            elif a['uses'].startswith('ssh://'):
                pu.fail("The ssh protocol is not supported yet.")
            else:
                url = 'https://github.com'
                service = 'github.com'
                parts = a['uses'].split('/')
                user = a['uses'].split('/')[0]
                repo = a['uses'].split('/')[1]
                action = '/'.join(a['uses'].split('/')[1:])

            if '@' in repo:
                action_dir = '/'.join(a['uses'].split('@')[-2].split('/')[-1:])
                version = a['uses'].split('@')[-1]
            elif '@' in action:
                action_dir = '/'.join(action.split('@')[-2].split('/')[-1:])
                version = action.split('@')[-1]
            else:
                action_dir = '/'.join(a['uses'].split('/')[2:])
                version = None
            action_dir = os.path.join('./', action_dir)

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
                    a, self.workspace, self.env,
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
                        a, self.workspace, self.env,
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
                    a, self.workspace, self.env,
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
                for future in as_completed(flist):
                    try:
                        future.result()
                        pu.info('Action ran successfully !\n')
                    except Exception:
                        sys.exit(1)
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
    def __init__(self, action, workspace, env, q, d, dry):
        super(DockerRunner, self).__init__(action, workspace, env, q, d, dry)
        self.cid = self.action['name'].replace(' ', '_')

    def run(self, reuse):
        build = True
        if 'docker://' in self.action['uses']:
            tag = self.action['uses'].replace('docker://', '')
            build = False
        elif './' in self.action['uses']:
            tag = 'action/' + os.path.basename(self.action['uses'])
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
        cmd_out, _ = pu.exec_cmd('docker ps -a',
                                 debug=self.debug, dry_run=self.dry_run)

        if self.cid in cmd_out:
            return True

        return False

    def docker_rm(self):
        pu.exec_cmd('docker rm {}'.format(self.cid),
                    debug=self.debug, dry_run=self.dry_run)

    def docker_create(self, img):
        env_vars = self.action.get('env', {})

        for s in self.action.get('secrets', []):
            env_vars.update({s: os.environ[s]})

        for e, v in self.env.items():
            env_vars.update({e: v})

        env_vars.update({'HOME': os.environ['HOME']})

        env_flags = [" -e {}='{}'".format(k, v) for k, v in env_vars.items()]

        docker_cmd = 'docker create '
        docker_cmd += ' --name={}'.format(self.cid)
        docker_cmd += ' --volume {0}:{0}'.format(self.workspace)
        docker_cmd += ' --volume {0}:{0}'.format(os.environ['HOME'])
        docker_cmd += ' --volume {0}:{0}'.format('/var/run/docker.sock')
        docker_cmd += ' --workdir={} '.format(self.workspace)
        docker_cmd += ''.join(env_flags)
        if self.action.get('runs', None):
            docker_cmd += ' --entrypoint={} '.format(self.action['runs'])
        docker_cmd += ' {}'.format(img)
        docker_cmd += ' {}'.format(' '.join(self.action.get('args', '')))

        pu.info('{}[{}] docker create {} {}\n'.format(
            self.msg_prefix,
            self.action['name'], img, ' '.join(self.action.get('args', ''))
        ))

        pu.exec_cmd(docker_cmd, debug=self.debug, dry_run=self.dry_run)

    def docker_start(self):
        pu.info('{}[{}] docker start \n'.format(self.msg_prefix,
                                                self.action['name']))

        cmd = 'docker start --attach {}'.format(self.cid)
        _, ecode = pu.exec_cmd(
            cmd, verbose=(not self.quiet), debug=self.debug,
            log_file=self.log_filename, dry_run=self.dry_run)
        return ecode

    def docker_pull(self, img):
        pu.info('{}[{}] docker pull {}\n'.format(self.msg_prefix,
                                                 self.action['name'], img))
        pu.exec_cmd('docker pull {}'.format(img),
                    debug=self.debug, dry_run=self.dry_run)

    def docker_build(self, tag, path):
        cmd = 'docker build -t {} {}'.format(tag, path)
        pu.info('{}[{}] {}\n'.format(self.msg_prefix,
                                     self.action['name'], cmd))
        pu.exec_cmd(cmd, debug=self.debug, dry_run=self.dry_run)


class SingularityRunner(ActionRunner):
    """Singularity Action Runner Class
    """

    def __init__(self, action, workspace, env, q, d, dry):
        super(SingularityRunner, self).__init__(action, workspace, env,
                                                q, d, dry)
        self.pid = self.action['name'].replace(' ', '_')
        Client.quiet=True

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

    def find_def_file(self, path):
        for file in os.listdir(path):
            if file.endswith('.def'):
                return file

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
            path,
            self.find_def_file(path)
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

    def run(self, reuse=False):
        cmd = self.action.get('runs', ['entrypoint.sh'])
        cmd[0] = os.path.join('./', cmd[0])
        cmd.extend(self.action.get('args', ''))

        cwd = os.getcwd()
        if not self.dry_run:
            if 'repo_dir' in self.action:
                os.chdir(self.action['repo_dir'])
            else:
                os.chdir(os.path.join(cwd, self.action['uses']))

        os.environ.update(self.action.get('env', {}))

        pu.info('{}[{}] {}\n'.format(self.msg_prefix, self.action['name'],
                                     ' '.join(cmd)))

        _, ecode = pu.exec_cmd(
            ' '.join(cmd), verbose=(not self.quiet), debug=self.debug,
            ignore_error=True, log_file=self.log_filename,
            dry_run=self.dry_run)

        for i in self.action.get('env', {}):
            os.environ.pop(i)

        os.chdir(cwd)

        if ecode != 0:
            pu.fail("\n\nAction '{}' failed.\n.".format(self.action['name']))
