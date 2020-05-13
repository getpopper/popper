import importlib
from popper._version import __popper_version__ as __version__

# check if dunamai is available
dunamai_spec = importlib.util.find_spec("dunamai")
dunamai_found = dunamai_spec is not None
if dunamai_found:
    # if dunamai is found, then we use it to display the version
    import dunamai

    __dev_version__ = dunamai.Version.from_any_vcs().serialize()
    # overwrite the __popper_version__ variable with new value
    __version__ = __dev_version__
