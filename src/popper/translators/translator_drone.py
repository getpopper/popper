from box.box import Box
from popper.translators.translator import WorkflowTranslator
from shlex import quote


class DroneTranslator(WorkflowTranslator):
    def __init__(self):
        super().__init__()

    def translate(self, wf):
        # get workflow type (Docker or Exec)
        wf_type = self._detect_type(wf)

        box = Box(kind="pipeline", type=wf_type, name="default")

        # environment variables available throughout the pipeline
        wf_env = {
            "GIT_COMMIT": "${DRONE_COMMIT_SHA}",
            "GIT_BRANCH": "${DRONE_COMMIT_BRANCH}",
            "GIT_SHA_SHORT": "${DRONE_COMMIT_SHA:0:7}",
            "GIT_REMOTE_ORIGIN_URL": "${DRONE_GIT_HTTP_URL}",
            "GIT_TAG": "${DRONE_TAG}:-''",  # use the empty string if the variable is undefined
        }

        if "options" in wf:
            if "env" in wf["options"]:
                wf_env = {**wf["options"]["env"], **wf_env}
        box["steps"] = [
            self._translate_step(step, wf_type, wf_env) for step in wf["steps"]
        ]
        return box.to_yaml()

    # given a popper workflow, detect the corresponding Drone's pipeline type
    def _detect_type(self, wf):
        if not wf["steps"]:
            raise AttributeError("`steps` must not be empty")

        # helper function that detects the type from Popper's `uses` field
        def detect_type(uses):
            if "docker://" in uses:
                return "docker"
            if uses == "sh":
                return "exec"
            raise AttributeError(f"Unexpected value {uses} found in `uses` attribute")

        # determine the types of each Popper step
        ts = [detect_type(step["uses"]) for step in wf["steps"]]

        # make sure all types are the same
        for t in ts[1:]:
            if ts[0] != t:
                raise AttributeError(
                    "Drone supports only one runner type per pipeline. Popper workflows that use both `sh` and Docker images cannot be translated."
                )
        return ts[0]

    def _translate_step(self, popper_step, wf_type, wf_env):
        drone_step = Box()
        drone_step["name"] = popper_step["id"]
        if wf_type == "docker":
            # set docker image
            drone_step["image"] = self._translate_uses(popper_step["uses"])

            # handle `dir` option
            # only with docker pipeline as `popper exec` does not respect this option with `uses: sh`
            if "dir" in popper_step:
                if not popper_step["runs"]:
                    raise AttributeError(
                        "Workflow with `dir` must specify `runs` to translation"
                    )
                drone_step["commands"] = [
                    # create a symbolic link to create the same the directry structure in Drone
                    "ln -s /drone/src /workspace",
                    # cd into the specified directory
                    f"cd {popper_step['dir']}",
                    # run the command
                    " ".join(
                        quote(arg)
                        for arg in list(popper_step["runs"]) + list(popper_step["args"])
                    ),
                ]
            # translate args and runs without modifications
            else:
                if "args" in popper_step:
                    drone_step["command"] = list(popper_step["args"])
                if "runs" in popper_step:
                    drone_step["entrypoint"] = list(popper_step["runs"])
        if wf_type == "exec":
            if not popper_step["runs"]:
                raise AttributeError("You must specify `runs` attribute for steps")

            # `commands` is an array of strings. Construct the command by concatenating `runs` and `args` and use it as the first and only element
            drone_step["commands"] = [
                " ".join(
                    quote(arg)
                    for arg in list(popper_step["runs"]) + list(popper_step["args"])
                )
            ]

        # because Drone only supports environment variables per pipeline in Docker pipelines, set variables in each step
        if "env" in popper_step:
            # if per-step variables are defined, merge them with pipeline-wide variables
            drone_step["environment"] = {**wf_env, **dict(popper_step["env"])}
        else:
            drone_step["environment"] = wf_env
        return drone_step

    def _translate_uses(self, uses):
        if "docker://" not in uses:
            raise AttributeError(
                "Only docker images are supported for Drone workflow translation"
            )
        img = uses.replace("docker://", "")
        return img
