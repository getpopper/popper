import os
import re

import git

from popper.cli import log


def new_repo():
    """Function to initialize a git.Repo object assumed to be in os.getcwd() or
    any parent directory.

    Args:
        None

    Returns:
        git.Repo: repo object or None if '.git/' not found in any parent folder
    """
    try:
        return git.Repo(search_parent_directories=True)
    except git.exc.InvalidGitRepositoryError:
        # Optimistically assume that this is due to .git/ folder not being
        # found, in which case all the methods in this module assume
        # os.getcwd() as the root of a project.
        pass
    return None


def get_project_root_folder(repo=None):
    """Function to find the project root folder.

    If the project is a git repository, the project root is the folder
    containing the `.git` folder, else the $PWD is assumed to be the
    project root.

    Args:
      None

    Returns:
      str: The path to the root of the project.

    """
    if repo:
        root_folder_path = repo.working_tree_dir
    else:
        root_folder_path = os.getcwd()

    return root_folder_path


def get_sha(repo):
    """Runs git rev-parse --short HEAD and returns result.

    This function returns 'unknown' if the project folder
    is not a git repo. It fails, when the project folder is a
    git repo but doesn't have any commit.

    Args:
        None

    Returns:
      str: The sha of the head commit or 'unknown'.

    """
    if repo:
        try:
            return repo.git.rev_parse(repo.head.object.hexsha, short=True)
        except ValueError as e:
            log.debug(e)
            log.fail(f'Could not obtain revision of repository located at {get_project_root_folder(repo)}'
                    )
    else:
        return 'na'


def get_remote_url(repo=None):
    """Obtains remote origin URL, if possible. Otherwise it returns empty str.

    Args:
        None

    Returns:
      str: The remote origin url or "".
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
    https://github.com/ by default.

    Args:
      url(str): The remote git repository hosting service url.
      org(str): The org/user to which the repo belongs.
      repo(str): The repo name.
      repo_dir(str): The path where to clone the repo.
      version(str, optional): The remote tag/branch to checkout. If version is
                              None, we use the default remote branch as version

    Returns:
        None

    """
    def get_default_branch(r):
        """
        Used to find default branch of the repository.

        Args:
          r: It is git.Repo object

        Returns:

        """
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

        # To obtain the authentication token if set as environment variable.
        auth_token = os.getenv('GITHUB_API_TOKEN')

        if(auth_token is not None and 'github' in url and '@' not in url):
            # To verify the link of github for private repo support.
            # The authentication token has to be added after protocol
            # The length of protocol is 8 in case of https://
            url = url[:8]+auth_token+'@'+url[8:]

        repo_url = f'{url}{org}/{repo}'
        cloned_repo = git.Repo.clone_from(repo_url, repo_dir)

    cloned_repo.git.checkout(get_default_branch(cloned_repo))
    cloned_repo.close()


def parse(url):
    """Method to parse the git url.

    Args:
      url(str): The url in string format.

    Returns:
        tuple(service_url, service, user, repo, step_dir, version)

    """

    if url.startswith('ssh://'):
        log.fail('The ssh protocol is not supported yet.')

    if url.endswith('.git'):
        url = url[:-4]

    pattern = re.compile(
        r'^(http://|https://|git@)?(?:(\w+\.\w+)(?:\/|\:))?'
        r'([\w\-]+)(?:\/([^\@^\/]+)\/?([^\@]+)?(?:\@([\w\W]+))?)$')

    try:
        protocol, service, user, repo, step_dir, version = pattern.search(
            url).groups()
    except AttributeError:
        log.fail(
            'Invalid url. The url should be in any of the 3 forms: \n'
            '1) https://github.com/user/repo/path/to/step@version \n'
            '2) gitlab.com/user/repo/path/to/step@version \n'
            '3) user/repo/path/to/step@version'
        )

    if not service:
        service = 'github.com'

    if not protocol:
        protocol = 'https://'

    if not step_dir:
        step_dir = ''

    service_url = protocol + service

    log.debug(f'parse("{url}"):')
    log.debug(f'  service_url: {service_url}')
    log.debug(f'  service: {service}')
    log.debug(f'  user: {user}')
    log.debug(f'  repo: {repo}')
    log.debug(f'  step_dir: {step_dir}')
    log.debug(f'  version: {version}')

    return service_url, service, user, repo, step_dir, version
