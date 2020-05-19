import importlib
import pathlib
import os
import sys

current_module = sys.modules[__name__]
print(current_module)

# check if dunamai is available
dunamai_spec = importlib.util.find_spec("dunamai")
dunamai_found = dunamai_spec is not None
if dunamai_found:
    # if dunamai is found, then we use it to display the version
    import dunamai

    __version__ = dunamai.Version.from_any_vcs().serialize()
    ver = f'__popper_version__ = "{__version__}"'
    _init_script_dir = pathlib.Path(__file__).parent.absolute()
    with open(_init_script_dir, "w") as v:
        v.write(ver)
else:
    from popper._version import __popper_version__ as __version__
