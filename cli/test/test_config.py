import unittest
import os

import utils as testutils

from popper.config import PopperConfig
from popper.cli import log


FIXDIR = f'{os.path.dirname(os.path.realpath(__file__))}/fixtures'


def _wfile(name, format):
    return f'{FIXDIR}/{name}.{format}'


class TestPopperConfig(unittest.TestCase):
    def setUp(self):
        log.setLevel('CRITICAL')
        self.test_dir = testutils.mk_repo().working_dir
        common_kwargs = {
            'skip_clone': False,
            'skip_pull': False,
            'dry_run': False,
            'workspace_dir': self.test_dir,
            'quiet': False,
            'reuse': False,
            'engine_options': dict(),
            'resman_options': dict()}

        self.from_config_file = PopperConfig(
            config_file=_wfile("settings_3", "yml"),
            engine=None,
            resource_manager=None,
            **common_kwargs)

        self.from_cli = PopperConfig(
            config_file=_wfile("settings_3", "yml"),
            engine='foo',
            resource_manager='bar',
            **common_kwargs)

        self.from_defaults = PopperConfig(
            config_file=None,
            engine=None,
            resource_manager=None,
            **common_kwargs)

        self.invalid_popper_cfg_one = PopperConfig(
            config_file=_wfile("settings_1", "yml"),
            engine=None,
            resource_manager=None,
            **common_kwargs)

        self.invalid_popper_cfg_two = PopperConfig(
            config_file=_wfile("settings_2", "yml"),
            engine=None,
            resource_manager=None,
            **common_kwargs)

    def tearDown(self):
        log.setLevel('NOTSET')

    def test_parse(self):
        self.assertEqual(
            self.from_config_file.config_from_file, 
            {
                'engine': {
                    'name': 'docker', 
                    'options': {'privileged': True}}, 
                
                'resource_manager': {
                    'name': 'slurm', 
                    'options': {'action_one': {'cpus-per-task': 1,'nodes': 1}}}
            })

    def test_validate(self):
        self.assertRaises(SystemExit, self.invalid_popper_cfg_one.validate)
        self.assertRaises(SystemExit, self.invalid_popper_cfg_two.validate)

    def test_normalize(self):
        # --engine and --resource manager not provided through cli
        # so, test those values get read from the config file.
        self.from_config_file.normalize()
        self.assertEqual(self.from_config_file.engine_name, 'docker')
        self.assertEqual(self.from_config_file.resman_name, 'slurm')
        self.assertEqual(self.from_config_file.engine_options, {'privileged': True})
        self.assertEqual(self.from_config_file.resman_options, {'action_one': {'nodes': 1, 'cpus-per-task': 1}})

        # --engine and --resource manager provided, config file is ignored.
        self.from_cli.normalize()
        self.assertEqual(self.from_cli.engine_name, 'foo')
        self.assertEqual(self.from_cli.resman_name, 'bar')

        # neither flags nor config flag describes what runtime/resman to use.
        self.from_defaults.normalize()
        self.assertEqual(self.from_defaults.engine_name, 'docker')
        self.assertEqual(self.from_defaults.resman_name, 'host')
        
