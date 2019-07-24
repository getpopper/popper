import os
import re

import git

from popper.cli import log


def init_repo_object():
    """Function to initialize the global repo
    object before every scm utility functions."""
    repo = None
    try:
        repo = git.Repo(search_parent_directories=True)
    except git.exc.InvalidGitRepositoryError:
        # Optimistically assume that this is due to .git/ folder not being
        # found, in which case all the methods in this module assume
        # os.getcwd() as the root of a project. This path will then be the
        # relative path used by actions (GITHUB_WORKSPACE variable).
        pass
    return repo


def get_git_root_folder():
    """Function to find the project root folder.

    If the project is a git repository, the project root is the folder
    containing the `.git` folder, else the $PWD is assumed to be the
    project root.

    Returns:
        str: The path to the root of the project.
    """
    repo = init_repo_object()
    if repo:
        root_folder_path = os.path.dirname(repo.git_dir)
    else:
        root_folder_path = os.getcwd()

    return root_folder_path


def get_name():
    """Function to find the name of the project repository.

    Assuming $PWD is part of a Git repository, it tries to find the name of
    the repository by looking at the 'origin' git remote. If no 'origin' remote
    is defined, it returns the name of the parent folder.

    Returns:
        str: The name of the project repository.
    """
    url = get_remote_url()
    if not url:
        return os.path.basename(get_git_root_folder())

    if url.endswith('.git'):
        url = url[:-4]

    return os.path.basename(url)


def get_user():
    """Function to find the user of a project repository.

    Assuming $PWD is part of a Git repository, it tries to find the user (or
    org) of the repository, as specified in the 'origin' git remote
    information. If the repository has not been pushed to a remote repo or if
    'origin' is not the name of any remote repository, it returns "".

    Returns:
        str: The user (or org) of the repository or "".
    """
    url = get_remote_url()
    if url:
        if 'https://' in url:
            return os.path.basename(os.path.dirname(url))
        else:
            return url.split(':')[1].split('/')[0]

    return ""


def get_ref():
    """Returns the Git REF pointed by .git/HEAD.

    If the project folder is not a git repo,
    'unknown' is returned.

    Returns:
        str: The head ref of the project repository or 'unknown'.
    """
    repo = init_repo_object()
    if repo:
        return "" if repo.head.is_detached else repo.head.ref.path
    else:
        return 'unknown'


def get_sha():
    """Runs git rev-parse --short HEAD and returns result.

    This function returns 'unknown' if the project folder
    is not a git repo. It fails, when the project folder is a
    git repo but doesn't have any commit.

    Returns:
        str: The sha of the head commit or 'unknown'.
    """
    repo = init_repo_object()
    if repo:
        try:
            return repo.git.rev_parse(repo.head.object.hexsha, short=True)
        except ValueError as e:
            log.debug(e)
            log.fail('Could not obtain revision of repository located at {}'
                     .format(get_git_root_folder()))
    else:
        return 'unknown'


def get_head_commit():
    """Returns the head commit object.

    If project folder is not a git repository, None is returned.
    Else, the head commit object is returned.

    Returns:
        git.objects.commit.Commit: The head commit object or None.
    """
    repo = init_repo_object()
    if repo:
        return repo.commit(get_sha())
    else:
        return None


def get_remote_url():
    """Obtains remote origin URL, if possible.
    Otherwise it returns empty str.

    Returns:
        str: The remote origin url or "".
    """
    repo = init_repo_object()
    url = ""
    if repo:
        if len(repo.remotes) > 0:
            url = repo.remotes.origin.url
        # cleanup the URL so we get in in https form and without '.git' ending
        if url.endswith('.git'):
            url = url[:-4]
        if 'git@' in url:
            url = 'https://' + url[4:].replace(':', '/')

    return url


def clone(url, org, repo, repo_dir, version=None):
    """Clones a repository using Git. The URL for the repo is
    https://github.com/ by default.

    Args:
        url (str): The remote git repository hosting service url.
        org (str): The org/user to which the repo belongs.
        repo (str): The repo name.
        repo_dir (str): The path where to clone the repo.
        version (str): The remote tag/branch to checkout.
                       If version is None, we use the default
                       remote branch as version.
    """
    def get_default_branch(r):
        if version:
            return version
        return r.remotes.origin.refs['HEAD'].ref.remote_head

    if os.path.exists(repo_dir):
        cloned_repo = git.Repo(repo_dir)
        cloned_repo.remotes.origin.pull(get_default_branch(cloned_repo))
    else:
        if '@' in url:
            url += ':'
        else:
            url += '/'

        repo_url = '{}{}/{}'.format(url, org, repo)
        cloned_repo = git.Repo.clone_from(repo_url, repo_dir)

    cloned_repo.git.checkout(get_default_branch(cloned_repo))


def get_git_files():
    """Used to return a list of files that are being tracked by
    git.

    If not a git tracked repository, None is returned.

    Returns:
        list: List of git tracked files or None.
    """
    repo = init_repo_object()
    if repo:
        return repo.git.ls_files().split("\n")
    else:
        return None


def parse(url):
    """Method to parse the git url.

    Args:
        url (str): The url in string format.

    Returns:
        tuple(service_url, service, user, repo, action_dir, version)
    """

    if url.startswith('ssh://'):
        log.fail('The ssh protocol is not supported yet.')

    if url.endswith('.git'):
        url = url[:-4]

    pattern = re.compile(
        r'^(http://|https://|git@)?(?:(\w+\.\w+)(?:\/|\:))?'
        r'([\w\-]+)(?:\/([^\@^\/]+)\/?([^\@]+)?(?:\@([\w\W]+))?)$')

    try:
        protocol, service, user, repo, action_dir, version = pattern.search(
            url).groups()
    except AttributeError:
        log.fail(
            'Invalid url. The url should be in any of the 3 forms: \n'
            '1) https://github.com/user/repo/path/to/action@version \n'
            '2) gitlab.com/user/repo/path/to/action@version \n'
            '3) user/repo/path/to/action@version'
        )

    if not service:
        service = 'github.com'

    if not protocol:
        protocol = 'https://'

    if not action_dir:
        action_dir = ''

    service_url = protocol + service

    log.debug('parse("{}"):'.format(url))
    log.debug('  service_url: {}'.format(service_url))
    log.debug('  service: {}'.format(service))
    log.debug('  user: {}'.format(user))
    log.debug('  repo: {}'.format(repo))
    log.debug('  action_dir: {}'.format(action_dir))
    log.debug('  version: {}'.format(version))

    return service_url, service, user, repo, action_dir, version
