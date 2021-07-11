from box.box import Box
from popper.translators.translator import WorkflowTranslator


class DroneTranslator(WorkflowTranslator):
    def __init__(self):
        super().__init__()

    def translate(self, wf):
        box = Box(kind="pipeline", type="docker", name="default")
        box["steps"] = list(map(self._translate_step, wf["steps"]))
        return box.to_yaml()

    def _translate_step(self, popper_step):
        drone_step = Box()
        drone_step["name"] = popper_step["id"]
        drone_step["image"] = self._translate_uses(popper_step["uses"])
        drone_step["command"] = list(popper_step["args"])
        drone_step["entrypoint"] = list(popper_step["runs"])
        return drone_step

    def _translate_uses(self, uses):
        if "docker://" not in uses:
            raise AttributeError(
                "Only docker images are supported for Drone workflow translation"
            )
        img = uses.replace("docker://", "")
        return img
