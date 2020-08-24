import os
import re

import git

from popper.cli import log


def new_repo(gitrepo_dir=None):
    """Function to initialize a git.Repo object for a repository that is
    assumed to be in gitrepo_dir, or any parent directory.

    Args:
        gitrepo_dir(str): path to a folder within a git repository folder

    Returns:
        git.Repo: repo object or None if '.git/' not found in any parent folder
    """
    if not gitrepo_dir or not os.path.isdir(gitrepo_dir):
        return None

    repo = None

    try:
        repo = git.Repo(gitrepo_dir, search_parent_directories=True)
    except git.InvalidGitRepositoryError:
        # Optimistically assume that this is due to .git/ folder not existing
        pass

    if not repo or is_empty(repo):
        return None

    return repo


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
        if url.endswith(".git"):
            url = url[:-4]
        if "git@" in url:
            url = "https://" + url[4:].replace(":", "/")

    return url


def clone(url, org, repo, repo_dir, version=None):
    """Clones a repository using Git. If ``repo_dir`` already exists, it pulls
    from the remote.

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
        return r.remotes.origin.refs["HEAD"].ref.remote_head

    if os.path.exists(repo_dir):
        cloned_repo = git.Repo(repo_dir)
        cloned_repo.remotes.origin.pull(get_default_branch(cloned_repo))
    else:
        if "@" in url:
            url += ":"
        else:
            url += "/"

        # To obtain the authentication token if set as environment variable.
        auth_token = os.getenv("GITHUB_API_TOKEN")

        if auth_token is not None and "github" in url and "@" not in url:
            # To verify the link of github for private repo support.
            # The authentication token has to be added after protocol
            # The length of protocol is 8 in case of https://
            url = url[:8] + auth_token + "@" + url[8:]

        repo_url = f"{url}{org}/{repo}"
        cloned_repo = git.Repo.clone_from(repo_url, repo_dir)

    cloned_repo.git.checkout(get_default_branch(cloned_repo))
    cloned_repo.close()


def parse(url):
    """Method to parse the git url. If a URL schema and hostname are not 
    included, it assumes ``https://github.com``.

    Args:
      url(str): The url in string format.

    Returns:
        tuple(service_url, service, user, repo, step_dir, version)

    """

    if url.startswith("ssh://"):
        log.fail("The ssh protocol is not supported yet.")

    if url.endswith(".git"):
        url = url[:-4]

    pattern = re.compile(
        r"^(http://|https://|git@)?(?:(\w+\.\w+)(?:\/|\:))?"
        r"([\w\-]+)(?:\/([^\@^\/]+)\/?([^\@]+)?(?:\@([\w\W]+))?)$"
    )

    try:
        protocol, service, user, repo, step_dir, version = pattern.search(url).groups()
    except AttributeError:
        log.fail(
            "Invalid url. The url should be in any of the 3 forms: \n"
            "1) https://github.com/user/repo/path/to/step@version \n"
            "2) gitlab.com/user/repo/path/to/step@version \n"
            "3) user/repo/path/to/step@version"
        )

    if not service:
        service = "github.com"

    if not protocol:
        protocol = "https://"

    if not step_dir:
        step_dir = ""

    service_url = protocol + service

    log.debug(f'parse("{url}"):')
    log.debug(f"  service_url: {service_url}")
    log.debug(f"  service: {service}")
    log.debug(f"  user: {user}")
    log.debug(f"  repo: {repo}")
    log.debug(f"  step_dir: {step_dir}")
    log.debug(f"  version: {version}")

    return service_url, service, user, repo, step_dir, version


def is_empty(repo):
    """True if the currently checked out branch has no commits."""
    return repo.git.rev_list("-n 1", "--all") == ""


def get_sha(repo, short=None):
    """Returns the commit id for the currently checked out version on the
    given repository object. If short is given, it is interpreted as the number
    of characters from the SHA that get returned. E.g. short=7 returns the
    first 7 characters, otherwise it returns the entire SHA1 string.
    """
    if not repo or is_empty(repo):
        return None

    if short:
        sha = repo.git.rev_parse(repo.head.object.hexsha, short=short)
    else:
        sha = repo.git.rev_parse(repo.head.object.hexsha)

    return sha


def get_branch(repo):
    """Get name of branch. If the repo is in detached head state, it looks for
    for environment variables commonly used in CI services: TRAVIS_BRANCH,
    GIT_BRANCH (Jenkins), CIRCLE_BRANCH and CI_COMMIT_REF_NAME (Gitlab)
    """
    if not repo or is_empty(repo):
        return None

    if not repo.head.is_detached:
        return repo.active_branch.name

    for v in ["TRAVIS_BRANCH", "GIT_BRANCH", "CIRCLE_BRANCH", "CI_COMMIT_REF_NAME"]:
        branch = os.environ.get(v)
        if branch:
            return branch

    return get_sha(repo)


def get_tag(repo):
    """Get name of tag for current commit. If current commit is not tagged,
    it looks for for environment variables commonly used in CI services:
    TRAVIS_TAG, CIRCLE_TAG, GIT_TAG (Jenkins) and CI_COMMIT_REF_NAME (Gitlab).
    """
    if not repo or is_empty(repo):
        return None

    tags = repo.git.tag("--points-at", "HEAD").split()

    if len(tags) > 0:
        return tags[0]

    for v in ["TRAVIS_TAG", "GIT_TAG", "CIRCLE_TAG", "CI_COMMIT_REF_NAME"]:
        tag = os.environ.get(v)
        if tag:
            return tag

    return None
