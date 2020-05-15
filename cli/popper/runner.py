import getpass
import importlib
import os
import sys

import popper.scm as scm
import popper.utils as pu

from popper.config import ConfigLoader
from popper.cli import log


class WorkflowRunner(object):
    """The workflow runner."""

    # class variable that holds references to runner singletons
    __runners = {}

    def __init__(self, config):
        self._config = config
        self._is_resman_module_loaded = False

    def _load_resman_module(self):
        """dynamically load resource manager module"""
        resman_mod_name = f"popper.runner_{self._config.resman_name}"
        resman_spec = importlib.util.find_spec(resman_mod_name)
        if not resman_spec:
            raise ValueError(f"Invalid resource manager: {self._config.resman_name}")
        self._resman_mod = importlib.import_module(resman_mod_name)
        self._is_resman_module_loaded = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        """calls __exit__ on all instantiated step runners"""
        if self._config.repo:
            self._config.repo.close()
        for _, r in WorkflowRunner.__runners.items():
            r.__exit__(exc_type, exc, traceback)
        WorkflowRunner.__runners = {}

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
        log.info(f"Got {sig} signal. Stopping running steps.")
        for _, runner in WorkflowRunner.__runners.items():
            runner.stop_running_tasks()
        sys.exit(0)

    def _process_secrets(self, wf):
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
        if self._config.dry_run or self._config.skip_clone:
            return

        for step in wf.steps:
            for s in step.secrets:
                if s not in os.environ:
                    if os.environ.get("CI", "") == "true":
                        log.fail(f"Secret {s} not defined")
                    else:
                        val = getpass.getpass(f"Enter the value for {s} : ")
                        os.environ[s] = val

    def _clone_repos(self, wf):
        """Clone steps that reference a repository.

        Args:
          wf(popper.parser.workflow): Instance of the Workflow class.
          config.dry_run(bool): True if workflow flag is being dry-run.
          config.skip_clone(bool): True if clonning step has to be skipped.
          config.wid(str): id of the workspace

        Returns:
            None
        """
        # cache directory for this workspace
        wf_cache_dir = os.path.join(self._config.cache_dir, self._config.wid)
        os.makedirs(wf_cache_dir, exist_ok=True)

        cloned = set()
        infoed = False

        for step in wf.steps:
            if (
                "docker://" in step.uses
                or "shub://" in step.uses
                or "library://" in step.uses
                or "./" in step.uses
                or step.uses == "sh"
            ):
                continue

            url, service, user, repo, step_dir, version = scm.parse(step.uses)

            repo_dir = os.path.join(wf_cache_dir, service, user, repo)

            if self._config.dry_run:
                continue

            if self._config.skip_clone:
                if not os.path.exists(repo_dir):
                    log.fail(f"Expecting folder '{repo_dir}' not found.")
                continue

            if not infoed:
                log.info("[popper] Cloning step repositories")
                infoed = True

            if f"{user}/{repo}" in cloned:
                continue

            log.info(f"[popper] - {url}/{user}/{repo}@{version}")
            scm.clone(url, user, repo, repo_dir, version)
            cloned.add(f"{user}/{repo}")

    def run(self, wf):
        """Run the given workflow.

        Args:
          wf(Workflow): workflow to be executed

        Returns:
            None
        """
        self._process_secrets(wf)
        self._clone_repos(wf)

        for step in wf.steps:
            log.debug(f"Executing step:\n{pu.prettystr(step)}")
            if step.uses == "sh":
                e = self._step_runner("host", step).run(step)
            else:
                e = self._step_runner(self._config.engine_name, step).run(step)

            if e != 0 and e != 78:
                log.fail(f"Step '{step.id}' failed ('{e}') !")

            log.info(f"Step '{step.id}' ran successfully !")

            if e == 78:
                break

        log.info(f"Workflow finished successfully.")

    def _step_runner(self, engine_name, step):
        """Factory of singleton runners"""
        if not self._is_resman_module_loaded:
            self._load_resman_module()

        runner = WorkflowRunner.__runners.get(engine_name, None)

        if not runner:
            engine_cls_name = f"{engine_name.capitalize()}Runner"
            engine_cls = getattr(self._resman_mod, engine_cls_name, None)
            if not engine_cls:
                raise ValueError(f"Cannot find class for {engine_name}")
            runner = engine_cls(config=self._config)
            WorkflowRunner.__runners[engine_name] = runner

        return runner


# class design guidelines:
# - if not exposed to users, then it is protected, e.g `_foo()`
# - if a method does not use internal state then it is a @staticmethod
# - if both of the above, then it's both protected and static
class StepRunner(object):
    """Base class for step runners, assumed to be singletons."""

    def __init__(self, config=None):
        if not config:
            self._config = ConfigLoader.load()
        else:
            self._config = config

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        pass

    def _prepare_environment(self, step, env={}):
        """Prepare environment variables for a step, which includes those in
        the 'env' and 'secrets' attributes.

        Args:
          step(dict): step information
          env(dict): optional environment to include in returned environment

        Returns:
          dict: key-value map of environment variables.
        """
        step_env = step.env.to_dict()
        for s in step.secrets:
            step_env.update({s: os.environ[s]})
        step_env.update(env)

        # define GIT_* variables
        if self._config.repo:
            step_env.update(
                {
                    "GIT_COMMIT": self._config.git_commit,
                    "GIT_BRANCH": self._config.git_branch,
                    "GIT_SHA_SHORT": self._config.git_sha_short,
                }
            )
        return step_env

    def stop_running_tasks(self):
        raise NotImplementedError("Needs implementation in derived classes.")

    def run(self, step):
        raise NotImplementedError("Needs implementation in derived classes.")
