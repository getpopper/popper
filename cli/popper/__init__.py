import importlib
import pathlib
import os


# check if dunamai is available
dunamai_spec = importlib.util.find_spec("dunamai")
dunamai_found = dunamai_spec is not None
if dunamai_found:
    # if dunamai is found, then we use it to display the version
    import dunamai

    __version__ = dunamai.Version.from_any_vcs().serialize()
    _ver = f'__popper_version__ = "{__version__}"'

    _init_script_dir = pathlib.Path(__file__).parent.absolute()
    _version_path_ = os.path.join(_init_script_dir, "_version.py")
    with open(_version_path_, "w") as v:
        v.write(_ver + "\n")
else:
    from popper._version import __popper_version__ as __version__
