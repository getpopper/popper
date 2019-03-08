import click
import os
import popper.utils as pu

from popper.cli import pass_context

ci_files = {
    'travis': {
        './.travis.yml': """
---
dist: xenial
language: python
python: 3.7
services: docker
install:
- git clone --recursive https://github.com/systemslab/popper /tmp/popper
- export PATH=$PATH:/tmp/popper/cli/bin
- export PYTHONUNBUFFERED=1
script: popper run --recursive
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
        git clone --recursive https://github.com/systemslab/popper /tmp/popper
        export PATH=$PATH:/tmp/popper/cli/bin
        export PYTHONUNBUFFERED=1
        popper run
"""
    },
    'jenkins': {
        './Jenkinsfile': """
---
stage ('Popper') {{ node {{
  sh "git clone --recursive https://github.com/systemslab/popper /tmp/popper"
  sh "export PATH=$PATH:/tmp/popper/cli/bin"
  sh "export PYTHONUNBUFFERED=1"
  sh "popper run --recursive
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
- git clone --recursive https://github.com/systemslab/popper /tmp/popper
- export PATH=$PATH:/tmp/popper/cli/bin

popper:
  script: popper run --recursive
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
@pass_context
def cli(ctx, service):
    """Generates configuration files for distinct CI services.
    """
    project_root = pu.get_project_root()

    if service not in ci_files:
        pu.fail("Unrecognized service " + service)

    for ci_file, ci_file_content in pu.get_items(ci_files[service]):
        ci_file_content = ci_file_content
        ci_file = os.path.join(project_root, ci_file)
        # create parent folder
        if not os.path.isdir(os.path.dirname(ci_file)):
            os.makedirs(os.path.dirname(ci_file))

        # write content
        with open(ci_file, 'w') as f:
            f.write(ci_file_content)

    pu.info('Wrote CI configuration file successfully\n')
