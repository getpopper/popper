import os
import git
import shutil
import popper.utils as pu


repo = None


def init_repo_object():
    global repo

    if repo is not None:
        return

    try:
        repo = git.Repo(search_parent_directories=True)
    except git.exc.InvalidGitRepositoryError:
        pu.fail('Unable to find root of a Git repository.\n')


def get_git_root_folder():
    """Tries to find the root folder.
    """
    init_repo_object()
    return os.path.dirname(repo.git_dir)


def get_popper_root_folder():
    """Tries to find the root folder of a popper repository. A Popper
    repository is where the .popper.yml is stored in.
    """
    root_folder = get_git_root_folder()

    if os.path.exists(os.path.join(root_folder, '.popper.yml')):
        return root_folder

    pu.fail(
        "Unable to find .popper.yml at {}. "
        "Run 'popper init' first.\n".format(root_folder))


def infer_repo_name_from_root_folder():
    """Finds the root folder of a local Github repository and returns it.

    Returns:
        repo_name (str): the name of the root folder.
    """
    init_repo_object()
    return os.path.basename(repo.git_dir)


def get_name():
    """Assuming $PWD is part of a Git repository, it tries to find the name of
    the repository by looking at the 'origin' git remote. If no 'origin' remote
    is defined, it returns the name of the parent folder.
    """
    url = get_remote_url()

    if not url:
        return infer_repo_name_from_root_folder()

    if url.endswith('.git'):
        url = url[:-4]

    return os.path.basename(url)


def get_user():
    """Assuming $PWD is part of a Git repository, it tries to find the user (or
    org) of the repository, as specified in the 'origin' git remote
    information. If the repository has not been pushed to a remote repo or if
    'origin' is not the name of any remote repository, returns None.
    """
    url = get_remote_url()
    if url:
        if 'https://' in url:
            return os.path.basename(os.path.dirname(url))
        else:
            return url.split(':')[1]

    return None


def get_ref():
    """Returns the Git REF pointed by .git/HEAD"""
    init_repo_object()
    return "" if repo.head.is_detached else repo.head.ref.path


def get_sha(debug):
    """Runs git rev-parse --short HEAD and returns result"""
    init_repo_object()
    try:
        return repo.git.rev_parse(repo.head.object.hexsha, short=True)
    except ValueError as e:
        if debug:
            print(e)
        pu.fail('Could not obtain revision of repository located at {}\n'
                .format(get_git_root_folder()))


def get_remote_url():
    """Obtains remote origin URL, if possible. Otherwise it returns empty str.
    """
    url = ""
    if len(repo.remotes) > 0:
        url = repo.remotes.origin.url
    # cleanup the URL so we get in in https form and without '.git' ending
    if url.endswith('.git'):
        url = url[:-4]
    if 'git@' in url:
        url = 'https://' + url[4:].replace(':', '/')

    return url


def clone(url, org, repo, repo_parent_dir, version=None, debug=False):
    """Clones a repository using Git. The URL for the repo is
    https://github.com/ by default. To override this, other URLs can be given
    by defining them in the 'action_urls' list specified in the .popper.yml
    file.
    """
    repo_dir = os.path.join(repo_parent_dir, repo)
    if os.path.exists(repo_dir):
        shutil.rmtree(repo_dir)

    if '@' in url:
        url += ':'
    else:
        url += '/'

    init_repo_object()

    git.Repo.clone_from(
        '{}{}/{}'.format(url, org, repo.split('@')[0]),
        os.path.join(repo_parent_dir, repo),
        depth=1,
        branch=version
    )


def get_git_files():
    """Used to return a list of files that are being tracked by
    git.

    Returns:
        files (list) : list of git tracked files
    """
    init_repo_object()
    return repo.git.ls_files().split("\n")
