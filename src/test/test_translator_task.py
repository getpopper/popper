from box import Box

from popper.translators.translator_task import TaskTranslator
from .test_common import PopperTest


class TestTaskTranslator(PopperTest):
    GIT_VARS = {
        "GIT_COMMIT": {"sh": 'git rev-parse HEAD || echo ""'},
        "GIT_BRANCH": {"sh": 'git branch --show-current 2>/dev/null || echo ""'},
        "GIT_SHA_SHORT": {"sh": 'git rev-parse --short HEAD 2>/dev/null || echo ""'},
        "GIT_REMOTE_ORIGIN_URL": {
            "sh": 'git config --get remote.origin.url || echo ""'
        },
        "GIT_TAG": {"sh": "git tag -l --contains HEAD 2>/dev/null | head -n 1"},
    }
    GIT_ENV = {
        "GIT_COMMIT": "{{.GIT_COMMIT}}",
        "GIT_BRANCH": "{{.GIT_BRANCH}}",
        "GIT_SHA_SHORT": "{{.GIT_SHA_SHORT}}",
        "GIT_REMOTE_ORIGIN_URL": "{{.GIT_REMOTE_ORIGIN_URL}}",
        "GIT_TAG": "{{.GIT_TAG}}",
    }
    GIT_ENV_FLAGS = "--env GIT_BRANCH --env GIT_COMMIT --env GIT_REMOTE_ORIGIN_URL --env GIT_SHA_SHORT --env GIT_TAG"

    def test_detect_type(self):
        tt = TaskTranslator()
        self.assertEqual(tt._detect_type("docker://alpine"), "docker")
        self.assertEqual(tt._detect_type("docker://alpine:latest"), "docker")
        self.assertEqual(tt._detect_type("sh"), "sh")
        with self.assertRaises(AttributeError):
            tt._detect_type("unknown")

    def test_translate_sh_step(self):
        tt = TaskTranslator()
        # basic
        self.assertEqual(
            tt._translate_sh_step(
                Box(
                    {
                        "id": "id",
                        "uses": "sh",
                        "runs": ["echo"],
                        "args": ["hello world"],
                    }
                )
            ),
            Box({"cmds": ["echo 'hello world'"]}),
        )
        # with env
        self.assertEqual(
            tt._translate_sh_step(
                Box(
                    {
                        "id": "id",
                        "uses": "sh",
                        "runs": ["echo"],
                        "args": ["hello world"],
                        "env": {"FOO": "foo", "BAR": "bar"},
                    }
                )
            ),
            Box({"cmds": ["echo 'hello world'"], "env": {"FOO": "foo", "BAR": "bar"},}),
        )
        # missing `runs`
        with self.assertRaises(AttributeError):
            tt._translate_sh_step(Box({"id": "id", "uses": "sh", "args": ["hello"]}))
        # without args
        self.assertEqual(
            tt._translate_sh_step(Box(id="id", uses="sh", runs=["echo"])),
            Box({"cmds": ["echo"]}),
        )

    def test_get_docker_image(self):
        tt = TaskTranslator()
        # image name only
        self.assertEqual(tt._get_docker_image("docker://alpine"), "alpine")
        # image name + tag
        self.assertEqual(
            tt._get_docker_image("docker://alpine:latest"), "alpine:latest"
        )
        # path to the directly (not supported)
        with self.assertRaises(AttributeError):
            tt._get_docker_image("./path/to/dir")

    def test_translate_docker_step(self):
        tt = TaskTranslator()
        # minimum
        self.assertEqual(
            tt._translate_docker_step(
                Box({"id": "id", "uses": "docker://hello-world",}), {},
            ),
            Box(
                {
                    "cmds": [
                        "docker run --rm -i --volume {{.PWD}}:/workspace --workdir /workspace hello-world"
                    ],
                }
            ),
        )
        # args + env
        self.assertEqual(
            tt._translate_docker_step(
                Box(
                    {
                        "id": "id",
                        "uses": "docker://node:14",
                        "args": ["index.js"],
                        "env": {"FOO": "foo", "BAR": "bar"},
                    }
                ),
                TestTaskTranslator.GIT_ENV,
            ),
            Box(
                {
                    "cmds": [
                        f"docker run --env BAR --env FOO {TestTaskTranslator.GIT_ENV_FLAGS} --rm -i --volume {{{{.PWD}}}}:/workspace --workdir /workspace node:14 index.js"
                    ],
                    "env": {"FOO": "foo", "BAR": "bar"},
                }
            ),
        )
        # runs
        self.assertEqual(
            tt._translate_docker_step(
                Box(
                    {
                        "id": "id",
                        "uses": "docker://alpine",
                        "runs": ["echo"],
                        "args": ["hello world"],
                    }
                ),
                {},
            ),
            Box(
                {
                    "cmds": [
                        "docker run --rm -i --volume {{.PWD}}:/workspace --workdir /workspace --entrypoint echo alpine 'hello world'"
                    ],
                }
            ),
        )
        # runs (two or more elements)
        self.assertEqual(
            tt._translate_docker_step(
                Box(
                    {
                        "id": "id",
                        "uses": "docker://alpine",
                        "runs": ["/bin/sh", "-c"],
                        "args": ["echo hello world"],
                    }
                ),
                {},
            ),
            Box(
                {
                    "cmds": [
                        "docker run --rm -i --volume {{.PWD}}:/workspace --workdir /workspace --entrypoint /bin/sh alpine -c 'echo hello world'"
                    ],
                }
            ),
        )
        # workdir
        self.assertEqual(
            tt._translate_docker_step(
                Box({"id": "id", "uses": "docker://hello-world", "dir": "/tmp"}), {}
            ),
            Box(
                {
                    "cmds": [
                        "docker run --rm -i --volume {{.PWD}}:/workspace --workdir /tmp hello-world"
                    ],
                }
            ),
        )

    def test_translate(self):
        tt = TaskTranslator()

        popper_wf_with_step_default = Box(
            {
                "steps": [
                    {
                        "id": "default",
                        "uses": "sh",
                        "runs": ["curl"],
                        "args": [
                            "-LO",
                            "https://github.com/datasets/co2-fossil-global/raw/master/global.csv",
                        ],
                    }
                ],
            }
        )
        with self.assertRaises(AttributeError):
            tt.translate(popper_wf_with_step_default)

        popper_wf_sh = Box(
            {
                "steps": [
                    {
                        "id": "download",
                        "uses": "sh",
                        "runs": ["curl"],
                        "args": [
                            "-LO",
                            "https://github.com/datasets/co2-fossil-global/raw/master/global.csv",
                        ],
                    }
                ],
            }
        )
        task_sh = tt.translate(popper_wf_sh)
        self.assertEqual(
            Box.from_yaml(task_sh),
            Box(
                {
                    "version": "3",
                    "vars": {"PWD": {"sh": "pwd"}, **TestTaskTranslator.GIT_VARS},
                    "env": {**TestTaskTranslator.GIT_ENV},
                    "tasks": {
                        "default": {"cmds": [{"task": "download"}]},
                        "download": {
                            "cmds": [
                                "curl -LO https://github.com/datasets/co2-fossil-global/raw/master/global.csv"
                            ]
                        },
                    },
                }
            ),
        )

        popper_wf_docker = Box(
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
                ],
            }
        )
        task_docker = tt.translate(popper_wf_docker)
        self.assertEqual(
            Box.from_yaml(task_docker),
            Box(
                {
                    "version": "3",
                    "vars": {"PWD": {"sh": "pwd"}, **TestTaskTranslator.GIT_VARS},
                    "env": {**TestTaskTranslator.GIT_ENV},
                    "tasks": {
                        "default": {"cmds": [{"task": "download"}]},
                        "download": {
                            "cmds": [
                                f"docker run {TestTaskTranslator.GIT_ENV_FLAGS} --rm -i --volume {{{{.PWD}}}}:/workspace --workdir /workspace byrnedo/alpine-curl:0.1.8 -LO https://github.com/datasets/co2-fossil-global/raw/master/global.csv"
                            ]
                        },
                    },
                }
            ),
        )
