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
    def __init__(self, wfile):
        if not os.path.isfile(wfile):
            pu.fail("File {} does not exist.\n".format(wfile))
        with open(wfile, 'r') as fp:
            self.wf = hcl.load(fp)

        self.workspace = '/tmp/workspace'
        self.timeout = 10800

        self.check_secrets()
        self.normalize()
        self.complete_graph()

    def normalize(self):
        """normalize the dictionary representation of the workflow"""
        _, wf_block = self.wf['workflow'].popitem()
        if type(wf_block['resolves']) == str:
            wf_block['resolves'] = [wf_block['resolves']]
        for _, a_block in self.wf['action'].items():
            if not a_block.get('needs', None):
                continue
            if type(a_block['needs']) == str:
                a_block['needs'] = [a_block['needs']]

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
            if not os.path.exists(repo_parent_dir):
                os.makedirs(repo_parent_dir)

            if not infoed:
                pu.info('[popper] cloning actions from repositories\n')
                infoed = True

            scm.clone(user, repo, repo_parent_dir, version)

            a['repo_dir'] = os.path.join(repo_parent_dir, repo)
            a['action_dir'] = action_dir

    def instantiate_runners(self):
        """Factory of ActionRunner instances, one for each action"""
        self.actions_cache_path = os.path.join(self.workspace, 'actions')
        self.download_actions()

        for _, a in self.wf['action'].items():
            if 'docker://' in a['uses']:
                a['runner'] = DockerRunner(a, self.workspace, self.timeout)
                continue

            if './' in a['uses']:
                if os.path.exists(os.path.join(a['uses'], 'Dockerfile')):
                    a['runner'] = DockerRunner(a, self.workspace, self.timeout)
                else:
                    a['runner'] = HostRunner(a, self.workspace, self.timeout)
                continue

            dockerfile_path = os.path.join(a['repo_dir'], a['action_dir'],
                                           'Dockerfile')

            if os.path.exists(dockerfile_path):
                a['runner'] = DockerRunner(a, self.workspace, self.timeout)
            else:
                a['runner'] = HostRunner(a, self.workspace, self.timeout)

    def run(self, action_name=None):
        """Run the pipeline or a specific action"""
        pu.exec_cmd('rm -rf {}/*'.format(self.workspace))
        os.environ['WORKSPACE'] = self.workspace

        self.instantiate_runners()

        if action_name:
            self.wf['action'][action_name]['runner'].run()
        else:
            for s in self.get_stages():
                self.run_stage(s)

    def run_stage(self, stage):
        # TODO: parallelize it
        for a in stage:
            self.wf['action'][a]['runner'].run()

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
    def __init__(self, action, workspace, timeout):
        self.action = action
        self.workspace = workspace
        self.timeout = timeout

        if not os.path.exists(self.workspace):
            os.makedirs(self.workspace)

    def run(self):
        raise NotImplementedError(
            "This method is required to be implemented in derived classes."
        )

    def execute(self, cmd, log_tag):
        time_limit = time.time() + self.timeout
        sleep_time = 0.25

        log_tag = log_tag.replace(' ', '_')

        out_fname = os.path.join(os.environ['WORKSPACE'], log_tag + '.out')
        err_fname = os.path.join(os.environ['WORKSPACE'], log_tag + '.err')

        with open(out_fname, "w") as outf, open(err_fname, "w") as errf:
            p = subprocess.Popen(cmd, stdout=outf, stderr=errf, shell=True,
                                 preexec_fn=os.setsid)

            while p.poll() is None:

                if self.timeout != 0.0 and time.time() > time_limit:
                    os.killpg(os.getpgid(p.pid), signal.SIGTERM)
                    sys.stdout.write(' time out!')
                    break

                if sleep_time < 300:
                    sleep_time *= 2

                for i in range(int(sleep_time)):
                    if i % 10 == 0:
                        pu.info('.')
                time.sleep(sleep_time)

        pu.info('\n')
        return p.poll()


class DockerRunner(ActionRunner):
    def __init__(self, action, workspace, timeout):
        super(DockerRunner, self).__init__(action, workspace, timeout)

    def run(self):
        if 'docker://' in self.action['uses']:
            img = self.action['uses'].strip('docker://')
            self.docker_pull(img)
            self.docker_run(img)
            return

        if './' in self.action['uses']:
            tag = 'action/' + os.path.basename(self.action['uses'])
            dockerfile_path = os.path.join(os.getcwd(), self.action['uses'])
        else:
            tag = '/'.join(self.action['uses'].split('/')[:2])
            dockerfile_path = os.path.join(self.action['repo_dir'],
                                           self.action['action_dir'])
        self.docker_build(tag, dockerfile_path)
        self.docker_run(tag)

    def docker_run(self, img):
        env_vars = self.action.get('env', {})

        for s in self.action.get('secrets', []):
            env_vars.update({s: os.environ[s]})

        env_flags = [' -e {}="{}"'.format(k, v) for k, v in env_vars.items()]

        docker_cmd = 'docker run --rm -v {0}:{0}'.format(self.workspace)
        docker_cmd += ' --workdir={} '.format(self.workspace)
        docker_cmd += ''.join(env_flags)
        if self.action.get('runs', None):
            docker_cmd += ' --entrypoint={} '.format(self.action['runs'])
        docker_cmd += ' {}'.format(img)
        docker_cmd += ' {}'.format(self.action.get('args', ''))

        pu.info('[{}] docker run {} {}'.format(self.action['name'], img,
                                               self.action.get('args', '')))

        self.execute(docker_cmd, self.action['name'])

    def docker_pull(self, img):
        pu.info('[{}] docker pull {}\n'.format(self.action['name'], img))
        pu.exec_cmd('docker pull {}'.format(img))

    def docker_build(self, tag, path):
        cmd = 'docker build -t {} {}'.format(tag, path)
        pu.info('[{}] {}\n'.format(self.action['name'], cmd))
        pu.exec_cmd(cmd)


class HostRunner(ActionRunner):
    def __init__(self, action, workspace, timeout):
        super(HostRunner, self).__init__(action, workspace, timeout)

    def run(self):
        cmd = [os.path.join('./', self.action.get('runs', 'entrypoint.sh'))]
        cmd.extend(self.action.get('args', []))

        cwd = os.getcwd()
        os.chdir(os.path.join(cwd, self.action['uses']))

        os.environ.update(self.action.get('env', {}))

        pu.info('[{}]  {}'.format(self.action['name'], ' '.join(cmd)))

        ecode = self.execute(' '.join(cmd), self.action['name'])

        for i in self.action.get('env', {}):
            os.environ.pop(i)

        os.chdir(cwd)

        if ecode != 0:
            pu.fail("\n\nAction '{}' failed.\n.".format(self.action['name']))
