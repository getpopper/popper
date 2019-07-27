import unittest
import os
import sys
import shutil

import requests_mock

from popper import utils as pu
from popper.cli import log


class TestUtils(unittest.TestCase):

    def setUp(self):
        log.setLevel('CRITICAL')

    def tearDown(self):
        log.setLevel('NOTSET')

    def test_get_items(self):
        sample_dict = {
            '1': 1,
            '2': 2
        }
        items = pu.get_items(sample_dict)
        for k, v in items:
            self.assertEqual(k, str(k))

    def test_decode(self):
        string = b'Hello from popper'
        result = pu.decode(string)
        if sys.version_info[0] == 2:
            self.assertIsInstance(result, unicode)
        else:
            self.assertIsInstance(result, str)

        string = 'Hello from popper'
        result = pu.decode(string)
        if sys.version_info[0] == 2:
            self.assertIsInstance(result, unicode)
        else:
            self.assertIsInstance(result, str)

    def test_sanitized_name(self):
        name = "test action"
        santizied_name = pu.sanitized_name(name)
        self.assertEqual(santizied_name, "test_action")

        name = "test@action"
        santizied_name = pu.sanitized_name(name)
        self.assertEqual(santizied_name, "test_action")

        name = "test(action)"
        santizied_name = pu.sanitized_name(name)
        self.assertEqual(santizied_name, "test_action_")

    def touch_file(self, path):
        open(path, 'w').close()

    def test_find_recursive_wfile(self):
        os.chdir('/tmp')
        os.makedirs('/tmp/one/two/three')
        self.touch_file('/tmp/one/a.workflow')
        self.touch_file('/tmp/one/two/b.workflow')
        self.touch_file('/tmp/one/two/three/c.workflow')

        wfiles = pu.find_recursive_wfile()
        self.assertListEqual(wfiles, [
            '/tmp/one/a.workflow',
            '/tmp/one/two/b.workflow',
            '/tmp/one/two/three/c.workflow'])

        shutil.rmtree('/tmp/one')

    def test_find_default_wfile(self):
        os.makedirs('/tmp/test_folder/.github')
        os.chdir('/tmp/test_folder')

        self.assertRaises(SystemExit, pu.find_default_wfile, None)
        self.assertRaises(SystemExit, pu.find_default_wfile, 'a.workflow')
        self.touch_file('/tmp/test_folder/.github/main.workflow')
        wfile = pu.find_default_wfile()
        self.assertEqual(wfile, '.github/main.workflow')

        shutil.rmtree('/tmp/test_folder')

    @requests_mock.mock()
    def test_read_search_sources(self, m):
        m.get('https://raw.githubusercontent.com/systemslab/popper/'
              'master/cli/resources/search_sources.yml', text='response')
        search_sources = pu.read_search_sources()
        self.assertEqual(search_sources, 'response')

    @requests_mock.mock()
    def test_fetch_readme_for_repo(self, m):
        m.get('https://raw.githubusercontent.com/actions/'
              'bin/master/sh/README.md', text='response')
        readme = pu.fetch_readme_for_repo('actions', 'bin', 'sh', 'master')
        self.assertEqual(readme, 'response')

        readme = pu.fetch_readme_for_repo('actions', 'bin', 'sh')
        self.assertEqual(readme, 'response')

    @requests_mock.mock()
    def test_fetch_repo_metadata(self, m):
        m.get('https://raw.githubusercontent.com/actions/'
              'bin/master/sh/README.md', text='response')
        metadata = pu.fetch_repo_metadata('actions', 'bin', 'sh', 'master')
        self.assertDictEqual(metadata, {'repo_readme': 'response'})

    @requests_mock.mock()
    def test_make_gh_request(self, m):
        m.get('http://sample.test', text='response', status_code=200)
        response = pu.make_gh_request('http://sample.test')
        self.assertEqual(response.text, 'response')

        m.get('http://sample.test', status_code=400)
        self.assertRaises(
            SystemExit,
            pu.make_gh_request,
            'http://sample.test',
            True)

    @requests_mock.mock()
    def test_fetch_metadata(self, m):
        m.get(
            'https://raw.githubusercontent.com/systemslab/popper/'
            'master/cli/resources/search_sources.yml',
            text='- popperized/cmake\n- popperized/ansible')

        m.get(
            'https://raw.githubusercontent.com/popperized/cmake/'
            'master/README.md',
            text='Cmake Readme')

        m.get(
            'https://raw.githubusercontent.com/popperized/ansible/'
            'master/README.md',
            text='Ansible Readme')

        cache_file = pu.setup_cache()
        if os.path.exists(cache_file):
            os.remove(cache_file)
        meta = pu.fetch_metadata()
        self.assertEqual(os.path.exists(cache_file), True)
        self.assertEqual(meta,
                         {
                             'popperized/cmake': {
                                 'repo_readme': 'Cmake Readme'
                             },
                             'popperized/ansible': {
                                 'repo_readme': 'Ansible Readme'
                             }
                         })
        os.remove(cache_file)
        meta = pu.fetch_metadata(update_cache=True)
        self.assertEqual(os.path.exists(cache_file), True)
        self.assertEqual(meta,
                         {
                             'popperized/cmake': {
                                 'repo_readme': 'Cmake Readme'
                             },
                             'popperized/ansible': {
                                 'repo_readme': 'Ansible Readme'
                             }
                         })

    def test_setup_cache(self):
        cache_file_path = pu.setup_cache()
        try:
            self.assertEqual(cache_file_path, os.path.join(
                os.environ['XDG_CACHE_HOME'],
                '.popper_cache.yml'
            ))
        except KeyError:
            self.assertEqual(cache_file_path, os.path.join(
                os.environ['HOME'],
                '.cache',
                '.popper_cache.yml'
            ))

    def test_of_type(self):
        param = [u"hello", u"world"]
        self.assertEqual(pu.of_type(param, ['los']), True)

        param = u"hello world"
        self.assertEqual(pu.of_type(param, ['los']), False)

        param = {
            "org": "systemslab",
            "project": "popper"
        }
        self.assertEqual(pu.of_type(param, ['str', 'dict']), True)
