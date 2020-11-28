import os
import yaml

import popper.scm as scm

from hashlib import shake_256
from popper.cli import log as log

from box import Box


class ConfigLoader(object):
    @staticmethod
    def load(
        engine_name=None,
        resman_name=None,
        config_file=None,
        workspace_dir=os.getcwd(),
        reuse=False,
        dry_run=False,
        quiet=False,
        skip_pull=False,
        skip_clone=False,
        pty=False,
        allow_undefined_secrets_in_ci=False,
    ):
        """Loads and creates a configuration, represented by a frozen Box
        """
        workspace_dir = os.path.realpath(workspace_dir)
        repo = scm.new_repo(workspace_dir)

        # path to cache
        if os.environ.get("POPPER_CACHE_DIR", None):
            cache_dir = os.environ["POPPER_CACHE_DIR"]
        else:
            cache_dir_default = os.path.join(os.environ["HOME"], ".cache")
            cache_dir = os.environ.get("XDG_CACHE_HOME", cache_dir_default)
            cache_dir = os.path.join(cache_dir, "popper")

        from_file = ConfigLoader.__load_config_from_file(
            config_file, engine_name, resman_name
        )

        pp_config = {
            "workspace_dir": workspace_dir,
            "reuse": reuse,
            "dry_run": dry_run,
            "quiet": quiet,
            "skip_pull": skip_pull,
            "skip_clone": skip_clone,
            "pty": pty,
            "allow_undefined_secrets_in_ci": allow_undefined_secrets_in_ci,
            # if no git repository exists in workspace_dir or its parents, the repo
            # variable is None and all git_* variables are assigned to 'na'
            "repo": repo,
            "git_commit": scm.get_sha(repo),
            "git_sha_short": scm.get_sha(repo, short=7),
            "git_branch": scm.get_branch(repo),
            "git_tag": scm.get_tag(repo),
            "git_remote_origin_url": scm.get_remote_url(repo),
            # wid is used to associate a unique id to this workspace. This is then
            # used by runners to name resources in a way that there is no name
            # clash between concurrent workflows being executed
            "wid": shake_256(workspace_dir.encode("utf-8")).hexdigest(4),
            "cache_dir": cache_dir,
            "engine_name": from_file["engine_name"],
            "resman_name": from_file["resman_name"],
            "engine_opts": from_file["engine_opts"],
            "resman_opts": from_file["resman_opts"],
        }

        return Box(pp_config, default_box=True, frozen_box=True)

    @staticmethod
    def __load_config_from_file(config_file, engine_name, resman_name):
        from_file = ConfigLoader.__load_config_file(config_file)
        loaded_conf = {}

        eng_section = from_file.get("engine", None)
        eng_from_file = from_file.get("engine", {}).get("name")
        if from_file and eng_section and not eng_from_file:
            log.fail("No engine name given.")

        resman_section = from_file.get("resource_manager", None)
        resman_from_file = from_file.get("resource_manager", {}).get("name")
        if from_file and resman_section and not resman_from_file:
            log.fail("No resource manager name given.")

        # set name in precedence order (or assigne default values)
        if engine_name:
            loaded_conf["engine_name"] = engine_name
        elif eng_from_file:
            loaded_conf["engine_name"] = eng_from_file
        else:
            loaded_conf["engine_name"] = "docker"

        if resman_name:
            loaded_conf["resman_name"] = resman_name
        elif resman_from_file:
            loaded_conf["resman_name"] = resman_from_file
        else:
            loaded_conf["resman_name"] = "host"

        engine_opts = from_file.get("engine", {}).get("options", {})
        resman_opts = from_file.get("resource_manager", {}).get("options", {})
        loaded_conf["engine_opts"] = engine_opts
        loaded_conf["resman_opts"] = resman_opts

        return loaded_conf

    @staticmethod
    def __load_config_file(config_file):
        """Validate and parse the engine configuration file.

        Args:
          config_file(str): Path to the file to be parsed.

        Returns:
          dict: Engine configuration.
        """
        if isinstance(config_file, dict):
            return config_file

        if not config_file:
            return dict()

        if not os.path.exists(config_file):
            log.fail(f"File {config_file} was not found.")

        if not config_file.endswith(".yml"):
            log.fail("Configuration file must be a YAML file.")

        with open(config_file, "r") as cf:
            data = yaml.load(cf, Loader=yaml.Loader)

        if not data:
            log.fail("Configuration file is empty.")

        return data
