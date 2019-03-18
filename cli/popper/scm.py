import os
import popper.utils as pu
import git


def infer_repo_name_from_root_folder():
    """Finds the root folder of a local Github repository and returns it.

    Returns:
        repo_name (str): the name of the root folder.
    """
    return os.path.basename(repo.git.rev_parse('--show-toplevel'))

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

def get_remote_url():
    """Obtains remote origin URL, if possible. Otherwise it returns empty str.
    """
    repo = git.Repo(search_parent_directories=True)
    url = repo.remotes.origin.url
    # cleanup the URL so we get in in https form and without '.git' ending
    if url.endswith('.git'):
        url = url[:-4]
    if 'git@' in url:
        url = 'https://' + url[4:].replace(':', '/')

    return url
