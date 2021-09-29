from box.box import Box
from popper.translators.translator import WorkflowTranslator
from shlex import quote


# helper function to quote and join strings
def quoteJoin(lst):
    return " ".join(quote(arg) for arg in lst)


class TaskTranslator(WorkflowTranslator):
    def __init__(self):
        super().__init__()

    def translate(self, wf):
        box = Box(version="3", tasks={}, vars={})

        box["vars"] = {
            "PWD": {"sh": "pwd"},
            # redirect stderr to /dev/null to supress warning if the directory is not a git repo
            "GIT_COMMIT": {"sh": 'git rev-parse HEAD || echo ""'},
            "GIT_BRANCH": {"sh": 'git branch --show-current 2>/dev/null || echo ""'},
            "GIT_SHA_SHORT": {
                "sh": 'git rev-parse --short HEAD 2>/dev/null || echo ""'
            },
            "GIT_REMOTE_ORIGIN_URL": {
                # git config --get exists with non-zero code if the config is not set.
                # if the remote origin url is not set, set the empty string
                # no need for redirect since it doesn't generate an error message
                "sh": 'git config --get remote.origin.url || echo ""'
            },
            "GIT_TAG": {"sh": "git tag -l --contains HEAD 2>/dev/null | head -n 1"},
        }

        box["env"] = {
            "GIT_COMMIT": "{{.GIT_COMMIT}}",
            "GIT_BRANCH": "{{.GIT_BRANCH}}",
            "GIT_SHA_SHORT": "{{.GIT_SHA_SHORT}}",
            "GIT_REMOTE_ORIGIN_URL": "{{.GIT_REMOTE_ORIGIN_URL}}",
            "GIT_TAG": "{{.GIT_TAG}}",
        }

        # translate each step
        for step in wf["steps"]:
            step_id = step["id"]
            if step_id == "default":
                raise AttributeError(
                    f"'default' cannot be used as a step ID when translating Popper to Task."
                )
            box["tasks"][step["id"]] = self._translate_step(step, box["env"])

        # call steps in order from default task
        box["tasks"]["default"] = {
            "cmds": [{"task": step["id"]} for step in wf["steps"]]
        }

        return box.to_yaml()

    # translate a step
    def _translate_step(self, step, env):
        t = self._detect_type(step["uses"])
        if t == "docker":
            return self._translate_docker_step(step, env)
        elif t == "sh":
            return self._translate_sh_step(step)

    # detect step type (docker or exec)
    def _detect_type(self, uses):
        if "docker://" in uses:
            return "docker"
        if uses == "sh":
            return "sh"
        raise AttributeError(f"Unexpected value {uses} found in `uses` attribute")

    # translate Popper steps to be executed on host
    def _translate_sh_step(self, step):
        task = Box()
        if "runs" not in step:
            # sh steps require `runs` attribute
            raise AttributeError("Expecting 'runs' attribute in step.")
        task["cmds"] = [
            quoteJoin(step["runs"] + (step["args"] if "args" in step else []))
        ]
        if "env" in step:
            task["env"] = step["env"]
        return task

    def _translate_docker_step(self, step, env):
        task = Box()

        # get the name of the docker image
        image = self._get_docker_image(step["uses"])

        # if `runs` is specified, override the entrypoint
        # --entrypoint can only take one component. append the rest to command_args
        # if not specified, set to None
        entrypoint = (
            f"--entrypoint {quote(step['runs'][0])}" if "runs" in step else None
        )

        # [COMMAND] [ARG]...
        command_args = []
        if "runs" in step:
            # if `runs` is specified, take the second and later arguments
            command_args = command_args + list(step["runs"][1:])
        if "args" in step:
            # if `args` is specified, append to the list
            command_args = command_args + list(step["args"])

        # get environment variables available in this step
        # both workflow-wide variables and step-specific variables are available thanks to the parser
        step_env = step["env"] if "env" in step else {}

        # a list of environment variables available in this context
        # sort the keys for readability and testability
        env_list = sorted(({**step_env, **env}).keys())
        # --env flags that make environment variables in Docker
        env_opt = " ".join([f"--env {varname}" for varname in env_list])

        # use specified value or default value
        workdir = step["dir"] if "dir" in step else "/workspace"

        # Falsy values (e.g. None, []) will be omitted
        command = [
            "docker",
            "run",
            env_opt,
            "--rm",
            "-i",
            "--volume {{.PWD}}:/workspace",
            f"--workdir {workdir}",
            entrypoint,
            image,
            quoteJoin(command_args),
        ]

        # omit falsy values and join without escapes
        task["cmds"] = [" ".join([i for i in command if i])]

        if step_env:
            task["env"] = step_env
        return task

    # takes a `uses` value and returns the name of the docker image
    def _get_docker_image(self, uses):
        if "docker://" not in uses:
            raise AttributeError(
                "Only docker images are supported for Task workflow translation"
            )
        img = uses.replace("docker://", "")
        return img
