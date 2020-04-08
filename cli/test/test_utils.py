import unittest
import os

from popper import utils as pu
from popper.cli import log


class TestUtils(unittest.TestCase):

    def setUp(self):
        log.setLevel('CRITICAL')

    def tearDown(self):
        log.setLevel('NOTSET')

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

    def test_assert_executable_exists(self):
        self.assertRaises(SystemExit, pu.assert_executable_exists, 'abcd')

    def test_select_not_none(self):
        a = ["Hello", {}, None]
        self.assertEqual(pu.select_not_none(a), "Hello")

        b = [{}, "Hello", []]
        self.assertEqual(pu.select_not_none(b), "Hello")

    def test_exec_cmd(self):
        cmd = ["echo", "command_1"]
        pid, ecode, output = pu.exec_cmd(cmd, logging=False)
        self.assertGreater(pid, 0)
        self.assertEqual(ecode, 0)
        self.assertEqual(output, "command_1\n")

        pid, ecode, output = pu.exec_cmd(cmd, logging=True)
        self.assertGreater(pid, 0)
        self.assertEqual(ecode, 0)
        self.assertEqual(output, "")

        pu.write_file("/tmp/test.py", "import os\nprint(os.environ['TEST'])")
        cmd = ["python", "test.py"]
        pid, ecode, output = pu.exec_cmd(
            cmd, env={'TEST': 'test'}, cwd="/tmp", logging=False)
        self.assertGreater(pid, 0)
        self.assertEqual(ecode, 0)
        self.assertEqual(output, "test\n")
