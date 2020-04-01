import os

from hashlib import shake_256

from popper.cli import log as log

import popper.scm as scm
import popper.utils as pu


class PopperConfig(object):
    def __init__(self, **kwargs):
        self.repo = scm.new_repo()
        self.workspace_dir = os.path.realpath(kwargs['workspace_dir'])
        self.wid = shake_256(self.workspace_dir.encode('utf-8')).hexdigest(4)
        self.workspace_sha = scm.get_sha(self.repo)
        self.config_file = kwargs['config_file']
        self.dry_run = kwargs['dry_run']
        self.skip_clone = kwargs['skip_clone']
        self.skip_pull = kwargs['skip_pull']
        self.quiet = kwargs['quiet']
        self.reuse = kwargs['reuse']
        self.engine_name = kwargs.get('engine', None)
        self.resman_name = kwargs.get('resource_manager', None)
        self.engine_options = kwargs['engine_options']
        self.resman_options = kwargs['resman_options']
        self.config_from_file = pu.load_config_file(self.config_file)

    def parse(self):
        self.validate()
        self.normalize()

    def validate(self):
        if self.config_from_file.get('engine', None):
            if not self.config_from_file['engine'].get('name', None):
                log.fail(
                    'engine config must have the name property.')

        if self.config_from_file.get('resource_manager', None):
            if not self.config_from_file['resource_manager'].get('name', None):
                log.fail(
                    'resource_manager config must have the name property.')

    def normalize(self):
        if not self.engine_name:
            if self.config_from_file.get('engine', None):
                self.engine_name = self.config_from_file['engine']['name']
                self.engine_options = self.config_from_file['engine'].get(
                    'options', dict())
            else:
                self.engine_name = 'docker'

        if not self.resman_name:
            if self.config_from_file.get('resource_manager', None):
                self.resman_name = self.config_from_file['resource_manager']['name']
                self.resman_options = self.config_from_file['resource_manager'].get(
                    'options', dict())
            else:
                self.resman_name = 'host'
