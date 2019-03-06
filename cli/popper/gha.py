from __future__ import unicode_literals
from builtins import dict, str
import hcl
import os
import popper.scm as scm
import popper.utils as pu
import signal
import subprocess
import time
import sys


class Workflow(object):
    """A GHA workflow.
    """
    def __init__(self, wfile, workspace):
        if not wfile:
            if os.path.isfile("main.workflow"):
                wfile = "main.workflow"
            elif os.path.isfile(".github/main.workflow"):
                wfile = ".github/main.workflow"

        if not wfile:
            pu.fail(
                "Files {} or {} not found.\n".format("./main.workflow",
                                                     ".github/main.workflow"))
        if not os.path.isfile(wfile):
            pu.fail("File {} not found.\n".format(wfile))

        with open(wfile, 'r') as fp:
            self.wf = hcl.load(fp)

        self.workspace = workspace
        self.timeout = 10800

        self.actions_cache_path = os.path.join('/', 'tmp', 'actions')

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
            'GITHUB_REF': scm.get_ref(),
        }

        for e in dict(self.env):
            self.env.update({e.replace('GITHUB_', 'POPPER_'): self.env[e]})

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
        for _, a_block in self.wf['action'].items():
            if a_block.get('needs', None):
                if isinstance(a_block['needs'], basestring):
                    a_block['needs'] = [a_block['needs']]
            if a_block.get('runs', None):
                if isinstance(a_block['runs'], basestring):
                    a_block['runs'] = [a_block['runs']]
            if a_block.get('args', None):
                if isinstance(a_block['args'], basestring):
                    a_block['args'] = a_block['args'].split()

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
            if 'docker://' in a['uses'] or './' in a['uses']:
                continue

            user = a['uses'].split('/')[0]
            repo = a['uses'].split('/')[1]

            if '@' in a['uses']:
                action_dir = '/'.join(a['uses'].split('@')[0].split('/')[2:])
                version = a['uses'].split('@')[1]
            else:
                action_dir = '/'.join(a['uses'].split('/')[2:])
                version = None
            action_dir = os.path.join('./', action_dir)

            repo_parent_dir = os.path.join(self.actions_cache_path, user)

            a['repo_dir'] = os.path.join(repo_parent_dir, repo)
            a['action_dir'] = action_dir

            if '{}/{}'.format(user, repo) in cloned:
                continue

            if not os.path.exists(repo_parent_dir):
                os.makedirs(repo_parent_dir)

            if not infoed:
                pu.info('[popper] cloning actions from repositories\n')
                infoed = True

            scm.clone(user, repo, repo_parent_dir, version)

            cloned.add('{}/{}'.format(user, repo))

    def instantiate_runners(self):
        """Factory of ActionRunner instances, one for each action"""
        for _, a in self.wf['action'].items():
            if 'docker://' in a['uses']:
                a['runner'] = DockerRunner(a, self.workspace,
                                           self.env, self.timeout)
                continue

            if './' in a['uses']:
                if os.path.exists(os.path.join(a['uses'], 'Dockerfile')):
                    a['runner'] = DockerRunner(a, self.workspace,
                                               self.env, self.timeout)
                else:
                    a['runner'] = HostRunner(a, self.workspace,
                                             self.env, self.timeout)
                continue

            dockerfile_path = os.path.join(a['repo_dir'], a['action_dir'],
                                           'Dockerfile')

            if os.path.exists(dockerfile_path):
                a['runner'] = DockerRunner(a, self.workspace,
                                           self.env, self.timeout)
            else:
                a['runner'] = HostRunner(a, self.workspace,
                                         self.env, self.timeout)

    def run(self, action_name=None, reuse=False):
        """Run the pipeline or a specific action"""
        os.environ['WORKSPACE'] = self.workspace

        self.download_actions()
        self.instantiate_runners()

        if action_name:
            self.wf['action'][action_name]['runner'].run(reuse)
        else:
            for s in self.get_stages():
                self.run_stage(s, reuse)

    def run_stage(self, stage, reuse=False):
        for a in stage:
            self.wf['action'][a]['runner'].run(reuse)

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
    def __init__(self, action, workspace, env, timeout):
        self.action = action
        self.workspace = workspace
        self.env = env
        self.timeout = timeout

        if not os.path.exists(self.workspace):
            os.makedirs(self.workspace)

        self.log_path = os.path.join(self.workspace, 'popper_logs')
        if not os.path.exists(self.log_path):
            os.makedirs(self.log_path)

    def run(self, reuse=False):
        raise NotImplementedError(
            "This method is required to be implemented in derived classes."
        )

    def execute(self, cmd, log_tag):
        time_limit = time.time() + self.timeout
        sleep_time = 0.25

        log_tag = log_tag.replace(' ', '_')

        out_fname = os.path.join(self.log_path, log_tag + '.out')
        err_fname = os.path.join(self.log_path, log_tag + '.err')

        with open(out_fname, "w") as outf, open(err_fname, "w") as errf:
            p = subprocess.Popen(cmd, stdout=outf, stderr=errf, shell=True,
                                 preexec_fn=os.setsid)

            while p.poll() is None:

                if self.timeout != 0.0 and time.time() > time_limit:
                    os.killpg(os.getpgid(p.pid), signal.SIGTERM)
                    sys.stdout.write(' time out!')
                    break

                if sleep_time < 30:
                    sleep_time *= 2

                for i in range(int(sleep_time)):
                    if i % 10 == 0:
                        pu.info('.')
                time.sleep(sleep_time)

        pu.info('\n')
        return p.poll()


class DockerRunner(ActionRunner):
    def __init__(self, action, workspace, env, timeout):
        super(DockerRunner, self).__init__(action, workspace, env, timeout)
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
        cmd_out = pu.exec_cmd('docker ps -a')

        if self.cid in cmd_out:
            return True

        return False

    def docker_rm(self):
        pu.exec_cmd('docker rm {}'.format(self.cid), ignoreerror=True)

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

        pu.info('[{}] docker create {} {}\n'.format(
            self.action['name'], img, ' '.join(self.action.get('args', '')))
        )

        pu.exec_cmd(docker_cmd)

    def docker_start(self):
        pu.info('[{}] docker start '.format(self.action['name']))

        cmd = 'docker start --attach {}'.format(self.cid)
        return self.execute(cmd, self.action['name'])

    def docker_pull(self, img):
        pu.info('[{}] docker pull {}\n'.format(self.action['name'], img))
        pu.exec_cmd('docker pull {}'.format(img))

    def docker_build(self, tag, path):
        cmd = 'docker build -t {} {}'.format(tag, path)
        pu.info('[{}] {}\n'.format(self.action['name'], cmd))
        pu.exec_cmd(cmd)


class HostRunner(ActionRunner):
    def __init__(self, action, workspace, env, timeout):
        super(HostRunner, self).__init__(action, workspace, env, timeout)

    def run(self, reuse=False):
        cmd = self.action.get('runs', ['entrypoint.sh'])
        cmd[0] = os.path.join('./', cmd[0])
        cmd.extend(self.action.get('args', ''))

        cwd = os.getcwd()
        os.chdir(os.path.join(cwd, self.action['uses']))

        os.environ.update(self.action.get('env', {}))

        pu.info('[{}] {}'.format(self.action['name'], ' '.join(cmd)))

        ecode = self.execute(' '.join(cmd), self.action['name'])

        for i in self.action.get('env', {}):
            os.environ.pop(i)

        os.chdir(cwd)

        if ecode != 0:
            pu.fail("\n\nAction '{}' failed.\n.".format(self.action['name']))
