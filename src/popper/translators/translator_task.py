from box.box import Box
from popper.translators.translator import WorkflowTranslator
from shlex import quote


# helper function to quote and join strings
def join(lst):
    return " ".join(quote(arg) for arg in lst)


class TaskTranslator(WorkflowTranslator):
    def __init__(self):
        super().__init__()

    def translate(self, wf):
        box = Box(version="3", tasks={}, vars={"PWD": {"sh": "pwd"}})

        # translate each step
        for step in wf["steps"]:
            box["tasks"][step["id"]] = self._translate_step(step)

        # call steps in order from default task
        box["tasks"]["default"] = {
            "cmds": [{"task": step["id"]} for step in wf["steps"]]
        }

        return box.to_yaml()

    # translate a step
    def _translate_step(self, step):
        t = self._detect_type(step["uses"])
        if t == "docker":
            return self._translate_docker_step(step)
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
        task["cmds"] = [join(step["runs"] + (step["args"] if "args" in step else []))]
        return task

    def _translate_docker_step(self, step):
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

        # use specified value or default value
        workdir = step["dir"] if "dir" in step else "/workspace"

        # Falsy values (e.g. None, []) will be omitted
        command = [
            "docker",
            "run",
            "--rm",
            "-i",
            "--volume {{.PWD}}:/workspace",
            f"--workdir {workdir}",
            entrypoint,
            image,
            join(command_args),
        ]

        # omit falsy values and join without escapes
        task["cmds"] = [" ".join([i for i in command if i])]
        return task

    # takes a `uses` value and returns the name of the docker image
    def _get_docker_image(self, uses):
        if "docker://" not in uses:
            raise AttributeError(
                "Only docker images are supported for Drone workflow translation"
            )
        img = uses.replace("docker://", "")
        return img
