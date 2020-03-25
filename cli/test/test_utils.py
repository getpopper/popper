import unittest
import os

from dotmap import DotMap

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
        os.remove('testfile1.txt')
        os.remove('testfile2.txt')

    def test_load_config_file(self):
        conf_content = """
engine:
    name: docker
    options:
        runtime: nvidia
        """
        pu.write_file('settings.yml', conf_content)
        config = pu.load_config_file('settings.yml')
        self.assertTrue(config.get('engine'), True)
        self.assertDictEqual(
            config['engine']['options'], {
                'runtime': 'nvidia'})
        os.remove('settings.yml')

    def test_assert_executable_exists(self):
        self.assertRaises(SystemExit, pu.assert_executable_exists, 'abcd')

    def test_select_not_none(self):
        a = ["Hello", {}, None]
        self.assertEqual(pu.select_not_none(a), "Hello")

        b = [DotMap(), "Hello", []]
        self.assertEqual(pu.select_not_none(b), "Hello")
