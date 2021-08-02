from click.testing import CliRunner
from box import Box

from popper import __version__
from popper import _version_file
from popper.commands import cmd_version
from popper.translators.translator_drone import DroneTranslator
from .test_common import PopperTest


class TestDroneTranslator(PopperTest):
    def test_detect_type(self):
        dt = DroneTranslator()
        # can detect docker pipeline
        self.assertEqual(
            dt._detect_type(
                Box(
                    {
                        "steps": [
                            {
                                "id": "1",
                                "uses": "docker://alpine",
                                "runs": ["echo"],
                                "args": ["step 1"],
                            },
                            {
                                "id": "2",
                                "uses": "docker://alpine",
                                "runs": ["echo"],
                                "args": ["step 2"],
                            },
                        ]
                    }
                )
            ),
            "docker",
        )

        # can detect exec pipeline
        self.assertEqual(
            dt._detect_type(
                Box(
                    {
                        "steps": [
                            {
                                "id": "1",
                                "uses": "sh",
                                "runs": ["echo"],
                                "args": ["step 1"],
                            },
                            {
                                "id": "2",
                                "uses": "sh",
                                "runs": ["echo"],
                                "args": ["step 2"],
                            },
                        ]
                    }
                )
            ),
            "exec",
        )

        # raise exception for empty steps
        with self.assertRaises(AttributeError):
            dt._detect_type(Box({"steps": []}))

        # raise exception for unknown type
        with self.assertRaises(AttributeError):
            dt._detect_type(
                Box(
                    {
                        "steps": [
                            {
                                "id": "1",
                                "uses": "UNKNOWN_TYPE",
                                "runs": ["echo"],
                                "args": ["step 1"],
                            }
                        ]
                    }
                )
            )

        # raise exception for mixed types
        with self.assertRaises(AttributeError):
            dt._detect_type(
                Box(
                    {
                        "steps": [
                            {
                                "id": "1",
                                "uses": "docker://alpine",
                                "runs": ["echo"],
                                "args": ["step 1"],
                            },
                            {
                                "id": "2",
                                "uses": "sh",
                                "runs": ["echo"],
                                "args": ["step 2"],
                            },
                        ]
                    }
                )
            )

    def test_translate_docker(self):
        dt = DroneTranslator()
        popper_wf = Box(
            {
                "options": {"env": {"FOO": "var1", "BAR": "var2",}},
                "steps": [
                    {
                        "id": "download",
                        "uses": "docker://byrnedo/alpine-curl:0.1.8",
                        "args": [
                            "-LO",
                            "https://github.com/datasets/co2-fossil-global/raw/master/global.csv",
                        ],
                        "env": {"BAZ": "var3"},
                    }
                ],
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
                            "environment": {
                                "GIT_COMMIT": "${DRONE_COMMIT_SHA}",
                                "GIT_BRANCH": "${DRONE_COMMIT_BRANCH}",
                                "GIT_SHA_SHORT": "${DRONE_COMMIT_SHA:0:7}",
                                "GIT_REMOTE_ORIGIN_URL": "${DRONE_GIT_HTTP_URL}",
                                "GIT_TAG": "${DRONE_TAG}:-''",
                                "FOO": "var1",
                                "BAR": "var2",
                                "BAZ": "var3",
                            },
                        }
                    ],
                }
            ),
        )

    def test_translate_exec(self):
        dt = DroneTranslator()
        popper_wf = Box(
            {
                "options": {"env": {"FOO": "var1", "BAR": "var2",}},
                "steps": [
                    {
                        "id": "download",
                        "uses": "sh",
                        "runs": ["curl"],
                        "args": [
                            "-LO",
                            "https://github.com/datasets/co2-fossil-global/raw/master/global.csv",
                        ],
                        "env": {"BAZ": "var3"},
                    }
                ],
            }
        )
        drone_wf = dt.translate(popper_wf)
        self.assertEqual(
            Box.from_yaml(drone_wf),
            Box(
                {
                    "kind": "pipeline",
                    "type": "exec",
                    "name": "default",
                    "steps": [
                        {
                            "name": "download",
                            "commands": [
                                "curl -LO https://github.com/datasets/co2-fossil-global/raw/master/global.csv"
                            ],
                            "environment": {
                                "GIT_COMMIT": "${DRONE_COMMIT_SHA}",
                                "GIT_BRANCH": "${DRONE_COMMIT_BRANCH}",
                                "GIT_SHA_SHORT": "${DRONE_COMMIT_SHA:0:7}",
                                "GIT_REMOTE_ORIGIN_URL": "${DRONE_GIT_HTTP_URL}",
                                "GIT_TAG": "${DRONE_TAG}:-''",
                                "FOO": "var1",
                                "BAR": "var2",
                                "BAZ": "var3",
                            },
                        }
                    ],
                }
            ),
        )

    def test_translate_optional(self):
        dt = DroneTranslator()
        popper_wf = Box({"steps": [{"id": "sample", "uses": "docker://alpine",}]})
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
                            "name": "sample",
                            "image": "alpine",
                            "environment": {
                                "GIT_COMMIT": "${DRONE_COMMIT_SHA}",
                                "GIT_BRANCH": "${DRONE_COMMIT_BRANCH}",
                                "GIT_SHA_SHORT": "${DRONE_COMMIT_SHA:0:7}",
                                "GIT_REMOTE_ORIGIN_URL": "${DRONE_GIT_HTTP_URL}",
                                "GIT_TAG": "${DRONE_TAG}:-''",
                            },
                        }
                    ],
                }
            ),
        )

    def test_translate_step_docker(self):
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
                "env": {"foo": "variable 1", "var": "variable 2",},
            }
        )
        wf_env = {"baz": "variable 3"}
        drone_step = dt._translate_step(popper_step, "docker", wf_env)
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
                    "environment": {
                        "foo": "variable 1",
                        "var": "variable 2",
                        "baz": "variable 3",
                    },
                }
            ),
        )

    def test_translate_step_dir(self):
        dt = DroneTranslator()
        popper_step = Box(
            {
                "id": "download",
                "uses": "docker://alpine",
                "dir": "/tmp",
                "runs": ["touch"],
                "args": ["file1", "file2"],
            }
        )
        drone_step = dt._translate_step(popper_step, "docker", {})
        self.assertEqual(
            drone_step,
            Box(
                {
                    "name": "download",
                    "image": "alpine",
                    "commands": [
                        "ln -s /drone/src /workspace",
                        "cd /tmp",
                        "touch file1 file2",
                    ],
                    "environment": {},
                }
            ),
        )

        popper_step_dir_without_runs = Box(
            {
                "id": "download",
                "uses": "docker://alpine",
                "dir": "/tmp",
                "args": ["echo", "missing runs"],
            }
        )
        with self.assertRaises(AttributeError):
            # raise an error if `runs` is empty
            dt._translate_step(popper_step_dir_without_runs, "docker", {})

    def test_translate_step_exec(self):
        dt = DroneTranslator()
        popper_step = Box(
            {
                "id": "download",
                "uses": "sh",
                "runs": ["curl"],
                "args": [
                    "-LO",
                    "https://github.com/datasets/co2-fossil-global/raw/master/global.csv",
                ],
                "env": {"foo": "variable 1", "var": "variable 2",},
            }
        )
        wf_env = {"baz": "variable 3"}
        drone_step = dt._translate_step(popper_step, "exec", wf_env)
        self.assertEqual(
            drone_step,
            Box(
                {
                    "name": "download",
                    "commands": [
                        "curl -LO https://github.com/datasets/co2-fossil-global/raw/master/global.csv"
                    ],
                    "environment": {
                        "foo": "variable 1",
                        "var": "variable 2",
                        "baz": "variable 3",
                    },
                }
            ),
        )

        popper_step_empty_runs = Box(
            {
                "id": "1",
                "uses": "sh",
                "runs": [],  # parser will create an empty array if `runs` is not specified
            }
        )
        with self.assertRaises(AttributeError):
            # raise an error if `runs` is empty
            dt._translate_step(popper_step_empty_runs, "exec", wf_env)

    def test_translate_step_optional(self):
        dt = DroneTranslator()
        # only "uses" attribute is required in Popper
        popper_step = Box(
            {
                "id": "1",  # this is optional but the Popper parser assigns a sequential id
                "uses": "docker://byrnedo/alpine-curl:0.1.8",
            }
        )
        drone_step = dt._translate_step(popper_step, "docker", {"foo": "var1"})
        self.assertEqual(
            drone_step,
            Box(
                {
                    "name": "1",
                    "image": "byrnedo/alpine-curl:0.1.8",
                    "environment": {"foo": "var1"},
                }
            ),
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
