from click.testing import CliRunner

from popper import __version__
from popper import _version_file
from popper.commands import cmd_version
from popper.translators.translator_drone import DroneTranslator
from .test_common import PopperTest


class TestDroneTranslator(PopperTest):
    def test_uses_non_docker(self):
        dt = DroneTranslator()
        with self.assertRaises(AttributeError):
            dt._translate_uses("./path/to/myimg/")

    def test_uses_docker_version(self):
        dt = DroneTranslator()
        image = dt._translate_uses("docker://alpine:3.9")
        self.assertEqual(image, "alpine:3.9")

    def test_uses_docker_latest(self):
        dt = DroneTranslator()
        image = dt._translate_uses("docker://alpine")
        self.assertEqual(image, "alpine")
