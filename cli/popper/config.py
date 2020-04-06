import os

from hashlib import shake_256

from popper.cli import log as log

import popper.scm as scm
import popper.utils as pu


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

        from_file = self.load_config_from_file(config_file, engine_name,
                                               resman_name)

        self.engine_name = from_file['engine_name']
        self.resman_name = from_file['resman_name']
        self.engine_opts = from_file['engine_opts']
        self.resman_opts = from_file['resman_opts']

    def load_config_from_file(self, config_file, engine_name, resman_name):
        from_file = pu.load_config_file(config_file)
        loaded_conf = {}

        eng_from_file = from_file.get('engine', {}).get('name')
        if from_file and not eng_from_file and not engine_name:
            log.fail('No engine name given.')

        resman_from_file = from_file.get('resource_manager', {}).get('name')
        if from_file and not resman_from_file and not resman_name:
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
