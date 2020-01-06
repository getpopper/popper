import os
import stat
from string import Template

import click

from popper import scm, utils as pu
from popper.cli import pass_context, log

base_script_content = """
#!/bin/bash
set -ex
"""

install_scripts_content = {
    'singularity': """
sudo apt-get update
sudo apt-get install -y build-essential \
                        libssl-dev \
                        uuid-dev \
                        libgpgme11-dev \
                        libseccomp-dev \
                        pkg-config \
                        squashfs-tools
mkdir -p ${GOPATH}/src/github.com/sylabs
cd ${GOPATH}/src/github.com/sylabs
git clone https://github.com/sylabs/singularity.git
cd singularity
git checkout v3.2.0
cd ${GOPATH}/src/github.com/sylabs/singularity
./mconfig
cd ./builddir
make
sudo make install
singularity version
cd $TRAVIS_BUILD_DIR
"""}

ci_files = {
    'travis': {
        './.travis.yml': Template("""
---
dist: xenial
language: python
python: 3.7
services: docker
$install_scripts
install:
- git clone https://github.com/systemslab/popper /tmp/popper
- export PYTHONUNBUFFERED=1
- pip install /tmp/popper/cli
script: popper run
""")
    },
    'circle': {
        './.circleci/config.yml': Template("""
---
version: 2
jobs:
  build:
    machine: true
    steps:
    - checkout
    - run:
        command: |
        $install_scripts
        git clone https://github.com/systemslab/popper /tmp/popper
        export PYTHONUNBUFFERED=1
        pip install /tmp/popper/cli
        popper run
""")
    },
    'jenkins': {
        './Jenkinsfile': Template("""
---
stage ('Popper') {{ node {{
  sh "git clone https://github.com/systemslab/popper /tmp/popper"
  sh "export PYTHONUNBUFFERED=1"
  sh "pip install /tmp/popper/cli"
  sh "popper run"
}}}}
""")
    },
    'gitlab': {
        '.gitlab-ci.yml': Template("""
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
""")
    },
    'brigade': {
        'brigade.js': Template("""
const { events, Job } = require("brigadier")
events.on("push", () => {
    var popper = new Job("popper", "python:3.7-slim-stretch")
    popper.tasks = [
        "apt-get update",
        "apt-get install -y git",
        $install_scripts
        "git clone https://github.com/systemslab/popper /tmp/popper",
        "export PYTHONUNBUFFERED=1",
        "pip install /tmp/popper/cli",
        "popper run"
    ]
    popper.run()
})
""")
    }
}


@click.command('ci', short_help='Generate CI service configuration files.')
@click.argument(
    'service',
    type=click.Choice(['travis', 'circle', 'jenkins', 'gitlab', 'brigade']),
    required=True
)
@click.option(
    '--install',
    help='Specify the runtime dependencies to install.',
    required=False,
    type=click.Choice(['singularity']),
    default=list(),
    multiple=True
)
@pass_context
def cli(ctx, service, install):
    """Generates configuration files for distinct CI services. This command
    needs to be executed on the root of your Git repository folder.
    """
    project_root = scm.get_git_root_folder()

    if project_root != os.getcwd():
        log.fail(
            'This command needs to be executed on the root of your '
            'Git project folder (where the .git/ folder is located).')

    for ci_file, ci_file_content in pu.get_items(ci_files[service]):

        # Prepare and write the CI config file.
        ci_file = os.path.join(project_root, ci_file)
        if not os.path.isdir(os.path.dirname(ci_file)):
            os.makedirs(os.path.dirname(ci_file))

        install_script_cmd = ''
        if install:
            if service == 'jenkins' or service == 'gitlab':
                log.fail(
                    'Scaffolding of custom install scripts is not '
                    'supported for Jenkins and Gitlab CI. Include it '
                    'manually depending upon the CI\'s OS.')

            elif service == 'travis':
                install_script_cmd = ('before_install: scripts/'
                                      'install_scripts.sh')

            elif service == 'circle':
                install_script_cmd = 'bash scripts/install_scripts.sh'

            elif service == 'brigade':
                install_script_cmd = '"bash scripts/install_scripts.sh",'

        with open(ci_file, 'w') as f:
            f.write(reformat(ci_file_content.safe_substitute(
                {'install_scripts': install_script_cmd})))

        # Prepare and Write the install scripts.
        if install:
            install = set(install)
            install_script_file = os.path.join(
                project_root, 'scripts', 'install_scripts.sh')
            script_content = base_script_content
            for runtime in install:
                script_content += install_scripts_content[runtime]

            if not os.path.isdir(os.path.dirname(install_script_file)):
                os.makedirs(os.path.dirname(install_script_file))

            with open(install_script_file, 'w') as f:
                f.write(script_content)

            st = os.stat(install_script_file)
            os.chmod(install_script_file, st.st_mode | stat.S_IEXEC)

    log.info('Wrote {} configuration successfully.'.format(service))


def reformat(config):
    return '\n'.join([s for s in config.splitlines() if s.strip()])
