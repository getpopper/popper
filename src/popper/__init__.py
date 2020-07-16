import importlib
import os

__version__ = "0.0.0"

_repo_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "..")
_version_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), "_version.py")

# check if dunamai is available
_dunamai_spec = importlib.util.find_spec("dunamai")
_dunamai_found = _dunamai_spec is not None

if _dunamai_found:

    # if dunamai is found, then we use it to display the version
    import dunamai

    # if codebase is inside a git repo, define GIT_DIR so dunamai gets the info for the
    # popper repo instead of wherever popper is being invoked from
    _git_dir = os.path.join(_repo_dir, ".git")

    if os.path.isdir(_git_dir):
        os.environ["GIT_DIR"] = _git_dir

    try:
        __version__ = dunamai.Version.from_git().serialize()
        _ver = f"__popper_version__ = '{__version__}'"
    except RuntimeError as e:
        # only raise if not a dunamai-raised error
        if "This does not appear to be a Git project" not in str(e):
            raise e

    with open(_version_file, "w") as v:
        v.write(_ver + "\n")

    # unset GIT_DIR
    os.environ.pop("GIT_DIR", None)

elif os.path.isfile(_version_file):
    # codebase not in a popper repo, and version file exists, so let's read from it
    from popper._version import __popper_version__ as _ver

    __version__ = _ver
