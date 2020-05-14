import unittest

from popper import utils as pu
from popper.cli import log


class TestUtils(unittest.TestCase):
    def setUp(self):
        log.setLevel("CRITICAL")

    def tearDown(self):
        log.setLevel("NOTSET")

    def test_sanitized_name(self):
        name = "test action"
        santizied_name = pu.sanitized_name(name, "1234")
        self.assertEqual(santizied_name, "popper_test_action_1234")

        name = "test@action"
        santizied_name = pu.sanitized_name(name, "1234")
        self.assertEqual(santizied_name, "popper_test_action_1234")

        name = "test(action)"
        santizied_name = pu.sanitized_name(name, "1234")
        self.assertEqual(santizied_name, "popper_test_action__1234")

    def test_assert_executable_exists(self):
        pu.assert_executable_exists("ls")
        self.assertRaises(SystemExit, pu.assert_executable_exists, "abcd")

    def test_kv_to_flag(self):
        self.assertEqual(pu.key_value_to_flag("x", "a"), "-x a")
        self.assertEqual(pu.key_value_to_flag("y", True), "-y")
        self.assertEqual(pu.key_value_to_flag("y", False), "")
        self.assertEqual(pu.key_value_to_flag("yy", True), "--yy")
        self.assertEqual(pu.key_value_to_flag("zz", "c"), "--zz c")
        eq = True
        self.assertEqual(pu.key_value_to_flag("x", "a", eq), "-x=a")
        self.assertEqual(pu.key_value_to_flag("y", True, eq), "-y=true")
        self.assertEqual(pu.key_value_to_flag("y", False, eq), "-y=false")
        self.assertEqual(pu.key_value_to_flag("yy", True, eq), "--yy=true")
        self.assertEqual(pu.key_value_to_flag("zz", "c", eq), "--zz=c")
