class WorkflowTranslator(object):
    """Base class for translators."""
    def __init__(self):
        pass

    def translate(self, wf):
        raise NotImplementedError("Needs implementation in derived classes.")

    @staticmethod
    def get_translator(service_name):
        from popper.translators.translator_drone import DroneTranslator
        from popper.translators.translator_task import TaskTranslator

        if service_name == "drone":
            return DroneTranslator()
        elif service_name == "task":
            return TaskTranslator()
        else:
            raise Exception(f"Unknown service {service_name}")
