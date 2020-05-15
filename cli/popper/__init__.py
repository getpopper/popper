import importlib
import os

# check if dunamai is available
dunamai_spec = importlib.util.find_spec("dunamai")
dunamai_found = dunamai_spec is not None
if dunamai_found:
    # if dunamai is found, then we use it to display the version
    import dunamai

    __version__ = dunamai.Version.from_any_vcs().serialize()
    ver = f'__popper_version__ = "{__version__}"'
    path = os.path.split(os.getcwd())
    if path[1] == "popper":
        version_path = os.path.join("cli", "popper", "_version.py")
    else:
        version_path = os.path.join("popper", "_version.py")
    with open(version_path, "w") as v:
        v.write(ver)
else:
    from popper._version import __popper_version__ as __version__
