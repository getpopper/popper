from click.testing import CliRunner
from box import Box

from popper import __version__
from popper import _version_file
from popper.commands import cmd_version
from popper.translators.translator_drone import DroneTranslator
from .test_common import PopperTest


class TestDroneTranslator(PopperTest):
    def test_translate(self):
        dt = DroneTranslator()
        popper_wf = Box(
            {
                "steps": [
                    {
                        "id": "download",
                        "uses": "docker://byrnedo/alpine-curl:0.1.8",
                        "args": [
                            "-LO",
                            "https://github.com/datasets/co2-fossil-global/raw/master/global.csv",
                        ],
                    }
                ]
            }
        )
        drone_wf = dt.translate(popper_wf)
        self.assertEqual(
            Box.from_yaml(drone_wf),
            Box(
                {
                    "kind": "pipeline",
                    "type": "docker",
                    "name": "default",
                    "steps": [
                        {
                            "name": "download",
                            "image": "byrnedo/alpine-curl:0.1.8",
                            "command": [
                                "-LO",
                                "https://github.com/datasets/co2-fossil-global/raw/master/global.csv",
                            ],
                        }
                    ],
                }
            ),
        )

    def test_translate_step(self):
        dt = DroneTranslator()
        popper_step = Box(
            {
                "id": "download",
                "uses": "docker://byrnedo/alpine-curl:0.1.8",
                "runs": ["curl"],
                "args": [
                    "-LO",
                    "https://github.com/datasets/co2-fossil-global/raw/master/global.csv",
                ],
            }
        )
        drone_step = dt._translate_step(popper_step)
        self.assertEqual(
            drone_step,
            Box(
                {
                    "name": "download",
                    "image": "byrnedo/alpine-curl:0.1.8",
                    "entrypoint": ["curl"],
                    "command": [
                        "-LO",
                        "https://github.com/datasets/co2-fossil-global/raw/master/global.csv",
                    ],
                }
            ),
        )

    def test_translate_step_optional(self):
        dt = DroneTranslator()
        # only "uses" attribute is required in Popper
        popper_step = Box(
            {
                "id": "1",  # this is optional but the Popper parser assigns a sequential id
                "uses": "docker://byrnedo/alpine-curl:0.1.8",
            }
        )
        drone_step = dt._translate_step(popper_step)
        self.assertEqual(
            drone_step, Box({"name": "1", "image": "byrnedo/alpine-curl:0.1.8",}),
        )

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
