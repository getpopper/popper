import unittest
import os
import shutil

from popper import utils as pu
from popper.cli import log


class TestUtils(unittest.TestCase):

    def setUp(self):
        log.setLevel('CRITICAL')

    def tearDown(self):
        log.setLevel('NOTSET')

    def test_decode(self):
        string = b'Hello from popper'
        result = pu.decode(string)
        self.assertIsInstance(result, str)

        string = 'Hello from popper'
        result = pu.decode(string)
        self.assertIsInstance(result, str)

    def test_sanitized_name(self):
        name = "test action"
        santizied_name = pu.sanitized_name(name, '1234')
        self.assertEqual(santizied_name, "popper_test_action_1234")

        name = "test@action"
        santizied_name = pu.sanitized_name(name, '1234')
        self.assertEqual(santizied_name, "popper_test_action_1234")

        name = "test(action)"
        santizied_name = pu.sanitized_name(name, '1234')
        self.assertEqual(santizied_name, "popper_test_action__1234")

    def touch_file(self, path):
        open(path, 'w').close()

    def test_find_recursive_wfile(self):
        os.makedirs('/tmp/one/two/three', exist_ok=True)
        os.chdir('/tmp')
        self.touch_file('/tmp/one/a.workflow')
        self.touch_file('/tmp/one/two/b.workflow')
        self.touch_file('/tmp/one/two/three/c.workflow')

        wfiles = pu.find_recursive_wfile()
        self.assertListEqual(wfiles, [
            '/tmp/one/a.workflow',
            '/tmp/one/two/b.workflow',
            '/tmp/one/two/three/c.workflow'])

        shutil.rmtree('/tmp/one')

    def test_setup_base_cache(self):
        cache_dir = pu.setup_base_cache()
        try:
            self.assertEqual(cache_dir, os.environ['XDG_CACHE_HOME'])
        except KeyError:
            self.assertEqual(
                cache_dir,
                os.path.join(
                    os.environ['HOME'],
                    '.cache/popper'))

        os.environ['POPPER_CACHE_DIR'] = '/tmp/popper'
        cache_dir = pu.setup_base_cache()
        self.assertEqual(cache_dir, '/tmp/popper')
        os.environ.pop('POPPER_CACHE_DIR')

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

    def test_write_file(self):
        content = "Hello world"
        pu.write_file('testfile1.txt', content)
        pu.write_file('testfile2.txt')
        with open('testfile1.txt', 'r') as f:
            self.assertEqual(f.read(), "Hello world")
        with open('testfile2.txt', 'r') as f:
            self.assertEqual(f.read(), '')

    def test_get_id(self):
        id = pu.get_id('abcd', 1234, 'efgh')
        self.assertEqual(id, 'cbae02068489f7577862718287862a3b')

    def test_parse_engine_configuration(self):
        conf = pu.parse_engine_configuration(None)
        self.assertEqual(conf, None)
        self.assertRaises(
            SystemExit,
            pu.parse_engine_configuration,
            'myconf.py')

        conf_content = """
- engine_configuration
        """
        pu.write_file('settings.yml', conf_content)
        self.assertRaises(
            SystemExit,
            pu.parse_engine_configuration,
            'settings.yml')

        conf_content = """
runtime_configuration = {
    "runtime": "nvidia"
}
        """
        pu.write_file('settings.py', conf_content)
        self.assertRaises(
            SystemExit,
            pu.parse_engine_configuration,
            'settings.py')

        conf_content = """
engine_configuration = {
    "runtime": "nvidia"
}
        """
        pu.write_file('settings.py', conf_content)
        config = pu.parse_engine_configuration('settings.py')
        self.assertDictEqual(config, {'runtime': 'nvidia'})
