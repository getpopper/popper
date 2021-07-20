from box.box import Box
from popper.translators.translator import WorkflowTranslator


class DroneTranslator(WorkflowTranslator):
    def __init__(self):
        super().__init__()

    def translate(self, wf):
        box = Box(kind="pipeline", type="docker", name="default")

        # environment variables available throughout the pipeline
        wf_env = {
            "GIT_COMMIT": "${DRONE_COMMIT_SHA}",
            "GIT_BRANCH": "${DRONE_COMMIT_BRANCH}",
            "GIT_SHA_SHORT": "${DRONE_COMMIT_SHA:0:7}",
            "GIT_REMOTE_ORIGIN_URL": "${DRONE_GIT_HTTP_URL}",
            "GIT_TAG": "${DRONE_TAG}",
        }

        if "options" in wf:
            if "env" in wf["options"]:
                wf_env = {**wf["options"]["env"], **wf_env}
        box["steps"] = [self._translate_step(step, wf_env) for step in wf["steps"]]
        return box.to_yaml()

    def _translate_step(self, popper_step, wf_env):
        drone_step = Box()
        drone_step["image"] = self._translate_uses(popper_step["uses"])
        drone_step["name"] = popper_step["id"]
        if "args" in popper_step:
            drone_step["command"] = list(popper_step["args"])
        if "runs" in popper_step:
            drone_step["entrypoint"] = list(popper_step["runs"])

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
