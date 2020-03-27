import getpass
import importlib
import os
import sys

from dotmap import DotMap

import popper.scm as scm
import popper.utils as pu

from popper.config import PopperConfig
from popper.cli import log


class WorkflowRunner(object):
    """The workflow runner."""

    # class variable that holds references to runner singletons
    runners = {}

    def __init__(self, engine, resource_manager, config_file=None,
                 workspace_dir=os.getcwd(), reuse=False, dry_run=False,
                 quiet=False, skip_pull=False, skip_clone=False):

        # create a config object from the given arguments
        kwargs = locals()
        kwargs.pop('self')
        self.config = PopperConfig(**kwargs)

        # dynamically load resource manager
        resman_mod_name = f'popper.runner_{self.config.resman_name}'
        resman_spec = importlib.util.find_spec(resman_mod_name)
        if not resman_spec:
            raise ValueError(
                f'Invalid resource manager: {self.config.resman_name}')
        self.resman_mod = importlib.import_module(resman_mod_name)

        log.debug(f'WorkflowRunner config:\n{pu.prettystr(self.config)}')

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        """calls __exit__ on all instantiated step runners"""
        self.config.repo.close()
        for _, r in WorkflowRunner.runners.items():
            r.__exit__(exc_type, exc, traceback)
        WorkflowRunner.runners = {}

    @staticmethod
    def signal_handler(sig, frame):
        """Handles the interrupt signal.

        Args:
            sig(int): Signal number of signal being passed to cli.
            frame(class):It represents execution frame. For more see
                https://docs.python.org/3/reference/datamodel.html

        Returns:
            None
        """
        log.info(f'Got {sig} signal. Stopping running steps.')
        for _, runner in WorkflowRunner.runners.items():
            runner.stop_running_tasks()
        sys.exit(0)

    @staticmethod
    def process_secrets(wf, config=DotMap({})):
        """Checks whether the secrets defined for a step are available in the
        execution environment. When the environment variable `CI` is set to
        `true` and no environment variable is defined for a secret, the
        execution fails, otherwise (CI not set or CI=false), it prompts the
        user to enter the values for undefined secrets. The processing is
        completely skipped if config.dry_run=True.

        Args:
          wf(popper.parser.Workflow): Instance of the Workflow class.
          config.dry_run(bool): skip execution of this function
          config.skip_clone(bool): skip execution of this function
        Returns:
            None
        """
        if config.dry_run or config.skip_clone:
            return

        for _, a in wf.steps.items():
            for s in a.get('secrets', []):
                if s not in os.environ:
                    if os.environ.get('CI', '') == 'true':
                        log.fail(f'Secret {s} not defined')
                    else:
                        val = getpass.getpass(
                            f'Enter the value for {s} : ')
                        os.environ[s] = val

    @staticmethod
    def clone_repos(wf, config):
        """Clone steps that reference a repository.

        Args:
          wf(popper.parser.workflow): Instance of the Workflow class.
          config.dry_run(bool): True if workflow flag is being dry-run.
          config.skip_clone(bool): True if clonning step has to be skipped.
          config.wid(str): id of the workspace

        Returns:
            None
        """
        repo_cache = os.path.join(pu.setup_base_cache(), config.wid)

        cloned = set()
        infoed = False

        for _, a in wf.steps.items():
            uses = a['uses']
            if 'docker://' in uses or './' in uses or uses == 'sh':
                continue

            url, service, user, repo, step_dir, version = scm.parse(
                a['uses'])

            repo_dir = os.path.join(repo_cache, service, user, repo)

            a['repo_dir'] = repo_dir
            a['step_dir'] = step_dir

            if config.dry_run:
                continue

            if config.skip_clone:
                if not os.path.exists(repo_dir):
                    log.fail(f"Expecting folder '{repo_dir}' not found.")
                continue

            if not infoed:
                log.info('[popper] Cloning step repositories')
                infoed = True

            if f'{user}/{repo}' in cloned:
                continue

            log.info(f'[popper] - {url}/{user}/{repo}@{version}')
            scm.clone(url, user, repo, repo_dir, version)
            cloned.add(f'{user}/{repo}')

    def run(self, wf):
        """Run the given workflow.

        Args:
          wf(Workflow): workflow to be executed

        Returns:
            None
        """
        WorkflowRunner.process_secrets(wf, self.config)
        WorkflowRunner.clone_repos(wf, self.config)

        for _, step in wf.steps.items():
            log.debug(f'Executing step:\n{pu.prettystr(step)}')
            if step['uses'] == 'sh':
                e = self.step_runner('host', step).run(step)
            else:
                e = self.step_runner(self.config.engine_name, step).run(step)

            if e != 0 and e != 78:
                log.fail(f"Step '{step['name']}' failed !")

            log.info(f"Step '{step['name']}' ran successfully !")

            if e == 78:
                break

        log.info(f"Workflow finished successfully.")

    def step_runner(self, engine_name, step):
        """Factory of singleton runners"""
        if engine_name not in WorkflowRunner.runners:
            engine_cls_name = f'{engine_name.capitalize()}Runner'
            engine_cls = getattr(self.resman_mod, engine_cls_name, None)
            if not engine_cls:
                raise ValueError(f'Unknown engine {engine_name}')
            WorkflowRunner.runners[engine_name] = engine_cls(self.config)
        return WorkflowRunner.runners[engine_name]


class StepRunner(object):
    """Base class for step runners, assumed to be singletons."""

    def __init__(self, config):
        self.config = config

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        pass

    @staticmethod
    def prepare_environment(step, env={}):
        """Prepare environment variables for a step, which includes those in
        the 'env' and 'secrets' attributes.

        Args:
          step(dict): step information
          env(dict): optional environment to include in returned environment

        Returns:
          dict: key-value map of environment variables.
        """
        step_env = step.get('env', {}).copy()
        for s in step.get('secrets', []):
            step_env.update({s: os.environ[s]})
        step_env.update(env)
        return step_env

    def stop_running_tasks(self):
        raise NotImplementedError("Needs implementation in derived classes.")

    def run(self, step):
        raise NotImplementedError("Needs implementation in derived classes.")
