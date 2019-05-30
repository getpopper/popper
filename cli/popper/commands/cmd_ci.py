import os

import click

from popper import scm, utils as pu
from popper.cli import pass_context, log

install_scripts = {
    'singularity': """wget http://neurodeb.pirsquared.org/\
pool/main/s/singularity-container/\
singularity-container_2.6.1-2~nd16.04+1_amd64.deb && \
sudo apt-get -f install ./singularity-container_2.6.1-2~nd16.04+1_amd64.deb"""}

ci_files = {
    'travis': {
        './.travis.yml': """
---
dist: xenial
language: python
python: 3.7
services: docker
install:
- git clone https://github.com/systemslab/popper /tmp/popper
- export PYTHONUNBUFFERED=1
- pip install /tmp/popper/cli
{}
script: popper run
"""
    },
    'circle': {
        './.circleci/config.yml': """
---
version: 2
jobs:
  build:
    machine: true
    steps:
    - checkout
    - run:
        command: |
        git clone https://github.com/systemslab/popper /tmp/popper
        export PYTHONUNBUFFERED=1
        pip install /tmp/popper/cli
        {}
        popper run
"""
    },
    'jenkins': {
        './Jenkinsfile': """
---
stage ('Popper') {{ node {{
  sh "git clone https://github.com/systemslab/popper /tmp/popper"
  sh "export PYTHONUNBUFFERED=1"
  sh "pip install /tmp/popper/cli"
  sh "popper run
}}}}
"""
    },
    'gitlab': {

        '.gitlab-ci.yml': """
---
image: docker:stable

variables:
  DOCKER_DRIVER: overlay

services:
- docker:dind

before_script:
- docker info
- apk update
- apk upgrade
- apk add python python-dev py-pip build-base git bash
- pip install virtualenv
- git clone https://github.com/systemslab/popper /tmp/popper
- pip install /tmp/popper/cli
popper:
  script: popper run
"""
    }
}


@click.command('ci', short_help='Generate CI service configuration files.')
@click.option(
    '--service',
    help='Name of CI service for which config files get generated.',
    type=click.Choice(['travis', 'circle', 'jenkins', 'gitlab']),
    required=True
)
@click.option(
    '--with-singularity',
    help='Add singularity install scripts in generated config files.',
    required=False,
    is_flag=True
)
@pass_context
def cli(ctx, service, with_singularity):
    """Generates configuration files for distinct CI services. This command
    needs to be executed on the root of your Git repository folder.
    """
    if service not in ci_files:
        log.fail("Unrecognized service " + service)

    project_root = scm.get_git_root_folder()

    if project_root != os.getcwd():
        log.fail(
            'This command needs to be executed on the root of your '
            'Git project folder (where the .git/ folder is located).')

    for ci_file, ci_file_content in pu.get_items(ci_files[service]):
        ci_file_content = ci_file_content
        ci_file = os.path.join(project_root, ci_file)
        # Create parent folder
        if not os.path.isdir(os.path.dirname(ci_file)):
            os.makedirs(os.path.dirname(ci_file))

        # Customize content
        scripts = []
        if with_singularity:
            if service in ['jenkins', 'gitlab']:
                log.fail(
                    'Scaffolding of Singularity install script is not '
                    'supported for Jenkins and Gitlab CI. Include it '
                    'manually depending upon the CI\'s OS.')
            scripts.append(install_scripts['singularity'])

        if scripts:
            scripts = ' && '.join(scripts)
            if service == 'travis':
                scripts = '- {}'.format(scripts)
        else:
            scripts = ''

        # Write content
        with open(ci_file, 'w') as f:
            f.write(reformat(ci_file_content.format(scripts)))

    log.info('Wrote {} configuration successfully.'.format(service))


def reformat(config):
    return '\n'.join([s for s in config.splitlines() if s.strip()])
