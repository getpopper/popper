import os
import yaml

import popper.scm as scm

from hashlib import shake_256
from popper.cli import log as log


class PopperConfig(object):
    def __init__(self, engine_name=None, resman_name=None, config_file=None,
                 workspace_dir=os.getcwd(), reuse=False,
                 dry_run=False, quiet=False, skip_pull=False,
                 skip_clone=False):

        self.workspace_dir = os.path.realpath(workspace_dir)
        self.reuse = reuse
        self.dry_run = dry_run
        self.quiet = quiet
        self.skip_pull = skip_pull
        self.skip_clone = skip_clone
        self.repo = scm.new_repo()
        self.workspace_sha = scm.get_sha(self.repo)

        wid = shake_256(self.workspace_dir.encode('utf-8')).hexdigest(4)
        self.wid = wid

        from_file = self._load_config_from_file(config_file, engine_name,
                                                resman_name)

        self.engine_name = from_file['engine_name']
        self.resman_name = from_file['resman_name']
        self.engine_opts = from_file['engine_opts']
        self.resman_opts = from_file['resman_opts']
        self.registry = from_file.get('registry', 'docker.io')

    def _load_config_from_file(self, config_file, engine_name, resman_name):
        from_file = PopperConfig.__load_config_file(config_file)
        loaded_conf = {}

        eng_section = from_file.get('engine', None)
        eng_from_file = from_file.get('engine', {}).get('name')
        if from_file and eng_section and not eng_from_file:
            log.fail('No engine name given.')

        resman_section = from_file.get('resource_manager', None)
        resman_from_file = from_file.get('resource_manager', {}).get('name')
        if from_file and resman_section and not resman_from_file:
            log.fail('No resource manager name given.')

        # set name in precedence order (or assigne default values)
        if engine_name:
            loaded_conf['engine_name'] = engine_name
        elif eng_from_file:
            loaded_conf['engine_name'] = eng_from_file
        else:
            loaded_conf['engine_name'] = 'docker'

        if resman_name:
            loaded_conf['resman_name'] = resman_name
        elif resman_from_file:
            loaded_conf['resman_name'] = resman_from_file
        else:
            loaded_conf['resman_name'] = 'host'

        engine_opts = from_file.get('engine', {}).get('options', {})
        resman_opts = from_file.get('resource_manager', {}).get('options', {})
        loaded_conf['engine_opts'] = engine_opts
        loaded_conf['resman_opts'] = resman_opts

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
            log.fail(f'File {config_file} was not found.')

        if not config_file.endswith('.yml'):
            log.fail('Configuration file must be a YAML file.')

        with open(config_file, 'r') as cf:
            data = yaml.load(cf, Loader=yaml.Loader)

        if not data:
            log.fail('Configuration file is empty.')

        return data
