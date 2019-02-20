import os
import popper.utils as pu


def get_repo_url():
    # TODO: add support for reading from 'action_repo_urls' from .popper.yml
    # NOTE: this has to return the URL in such a way that only repo/user needs
    #       to be appended to the returned string. That is, this has to return
    #       'https://github.com/' and not 'https://github.com' (former has a
    #       trailing '/'). Similar for other protocols.
    return 'https://github.com/'


def clone(org, repo, repo_parent_dir, version=None):
    """Clones a repository using Git. The URL of for the repo is
    https://github.com by default. To override this, other URLs can be given by
    defining them in the 'action_urls' list specified in the .popper.yml file.
    """
    repo_dir = os.path.join(repo_parent_dir, repo)
    if os.path.exists(repo_dir):
        pu.exec_cmd('rm -rf {}'.format(repo_dir))

    cmd = 'git -C {} clone --depth=1 {}{}/{}'.format(
        repo_parent_dir, get_repo_url(), org, repo)

    pu.exec_cmd(cmd)

    if version:
        pu.exec_cmd('git checkout {}'.format(version))
