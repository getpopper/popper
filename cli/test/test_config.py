import os

from popper.config import PopperConfig
from popper.cli import log

from .test_common import PopperTest


class TestPopperConfig(PopperTest):
    default_args = {
        'skip_clone': False,
        'engine_name': 'docker',
        'engine_opts': {},
        'resman_name': 'host',
        'resman_opts': {},
        'skip_pull': False,
        'dry_run': False,
        'workspace_dir': os.getcwd(),
        'quiet': False,
        'reuse': False
    }

    def setUp(self):
        log.setLevel('CRITICAL')
        self.maxDiff = None

    def tearDown(self):
        log.setLevel('NOTSET')

    def test_config_defaults(self):
        conf = PopperConfig()
        actual = conf.__dict__

        expected = TestPopperConfig.default_args

        self.assertEqual(expected,
                         TestPopperConfig.extract_dict(expected, actual))

    def test_config_non_defaults(self):
        expected = {
            'skip_clone': True,
            'skip_pull': True,
            'dry_run': True,
            'workspace_dir': os.path.realpath('/tmp/foo'),
            'quiet': True,
            'reuse': True
        }
        conf = PopperConfig(**expected)
        actual = conf.__dict__

        self.assertEqual(expected,
                         TestPopperConfig.extract_dict(expected, actual))

    def test_config_without_git_repo(self):
        conf = PopperConfig(workspace_dir='/tmp/foo')
        self.assertEqual('na', conf.git_commit)
        self.assertEqual('na', conf.git_branch)
        self.assertEqual('na', conf.git_sha_short)

    def test_config_with_git_repo(self):
        r = self.mk_repo()
        conf = PopperConfig(workspace_dir=r.working_dir)
        sha = r.head.object.hexsha
        self.assertEqual(r.git.rev_parse(sha), conf.git_commit)
        self.assertEqual(r.git.rev_parse(sha, short=7), conf.git_sha_short)
        self.assertEqual(r.active_branch.name, conf.git_branch)

    def test_config_from_file(self):
        config = {
            'engine': {'options': {'privileged': True}},
            'resource_manager': {'options': {'foo': 'bar'}}
        }
        kwargs = {'config_file': config}

        # engine name missing
        with self.assertLogs('popper', level='INFO') as cm:
            self.assertRaises(SystemExit, PopperConfig,  **kwargs)
            self.assertEqual(len(cm.output), 1)
            self.assertTrue('No engine name given' in cm.output[0])

        # resman name missing
        config.update({'engine': {'name': 'foo'}})
        with self.assertLogs('popper', level='INFO') as cm:
            self.assertRaises(SystemExit, PopperConfig,  **kwargs)
            self.assertEqual(len(cm.output), 1)
            self.assertTrue('No resource manager name given' in cm.output[0])

        # now all OK
        config.update({'resource_manager': {'name': 'bar'}})
        conf = PopperConfig(**kwargs)
        self.assertEqual(conf.engine_name, 'foo')
        self.assertEqual(conf.resman_name, 'bar')
        self.assertEqual(conf.engine_opts, {})
        self.assertEqual(conf.resman_opts, {})

        config.update({'engine': {'name': 'bar', 'options': {'foo': 'baz'}}})
        conf = PopperConfig(**kwargs)
        self.assertEqual(conf.engine_opts, {'foo': 'baz'})

    @staticmethod
    def extract_dict(A, B):
        # taken from https://stackoverflow.com/a/21213251
        return dict([(k, B[k]) for k in A.keys() if k in B.keys()])
