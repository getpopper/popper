import os
import popper.utils as pu


def get_repo_url():
    return 'https://github.com/'


def clone(org, repo, repo_parent_dir, version=None):
    """Clones a repository using Git. The URL for the repo is
    https://github.com/ by default. To override this, other URLs can be given
    by defining them in the 'action_urls' list specified in the .popper.yml
    file.
    """
    repo_dir = os.path.join(repo_parent_dir, repo)
    if os.path.exists(repo_dir):
        pu.exec_cmd('rm -rf {}'.format(repo_dir))

    cmd = 'git -C {} clone --depth=1 {}{}/{} &> /dev/null'.format(
        repo_parent_dir, get_repo_url(), org, repo)

    pu.exec_cmd(cmd)

    if version:
        pu.exec_cmd('git checkout {} &> /dev/null'.format(version))
