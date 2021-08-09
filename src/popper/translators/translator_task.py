from box.box import Box
from popper.translators.translator import WorkflowTranslator


class TaskTranslator(WorkflowTranslator):
    def __init__(self):
        super().__init__()

    def translate(self, wf):
        box = Box(version="3")
        return box.to_yaml()
