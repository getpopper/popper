import os
import re
import shutil
import git
from popper.cli import log

repo = None


def init_repo_object():
    global repo

    if repo is not None:
        return

    try:
        repo = git.Repo(search_parent_directories=True)
    except git.exc.InvalidGitRepositoryError:
        log.warn('Unable to find root of a Git repository.')


def get_git_root_folder():
    """Tries to find the root folder.
    """
    init_repo_object()
    if repo:
        root_folder_path = os.path.dirname(repo.git_dir)
    else:
        root_folder_path = os.getcwd()

    return root_folder_path


def infer_repo_name_from_root_folder():
    """Finds the root folder of a local Github repository and returns it.

    Returns:
        repo_name (str): the name of the root folder.
    """
    init_repo_object()
    if repo:
        repo_name = repo.git_dir
    else:
        repo_name = os.getcwd()

    return os.path.basename(repo_name)


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
    if repo:
        return "" if repo.head.is_detached else repo.head.ref.path
    else:
        return 'unknown'


def get_sha():
    """Runs git rev-parse --short HEAD and returns result"""
    init_repo_object()
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
    """Returns the head commit object."""
    init_repo_object()
    if repo:
        return repo.commit(get_sha())
    else:
        return None


def get_remote_url():
    """Obtains remote origin URL, if possible. Otherwise it returns empty str.
    """
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
    https://github.com/ by default. To override this, other URLs can be given
    by defining them in the 'action_urls' list specified in the .popper.yml
    file.
    """
    if os.path.exists(repo_dir):
        cloned_repo = git.Repo(repo_dir)
        cloned_repo.remotes.origin.pull(version)
        return

    if '@' in url:
        url += ':'
    else:
        url += '/'

    init_repo_object()

    repo_url = '{}{}/{}'.format(url, org, repo)

    git_args = {'depth': 1}

    if version:
        git_args['branch'] = version

    git.Repo.clone_from(repo_url, repo_dir, **git_args)


def get_git_files():
    """Used to return a list of files that are being tracked by
    git.

    Returns:
        files (list) : list of git tracked files
    """
    init_repo_object()
    if repo:
        return repo.git.ls_files().split("\n")
    else:
        return None


def parse(url):
    """Method to parse the git url.

    Args:
        url (str) : The url in string format.

    Returns:
        service_url, service, user, repo, action_dir, version
    """

    if url.startswith('ssh://'):
        log.fail('The ssh protocol is not supported yet.')

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
