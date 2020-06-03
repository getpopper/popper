import click
import os

from popper.cli import pass_context, log

ci_files = {
    # ##########################################################3
    "travis": {
        "./.travis.yml": """
---
dist: xenial
language: python
python: 3.7
services: docker
install:
- git clone https://github.com/systemslab/popper /tmp/popper
- export PYTHONUNBUFFERED=1
- pip install /tmp/popper/cli
script: popper run -f {}
"""
    },
    # ##########################################################3
    "circle": {
        "./.circleci/config.yml": """
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
        popper run -f {}
"""
    },
    # ##########################################################3
    "jenkins": {
        "./Jenkinsfile": """
---
stage ('Popper') {{ node {{
  sh "git clone https://github.com/systemslab/popper /tmp/popper"
  sh "export PYTHONUNBUFFERED=1"
  sh "pip install /tmp/popper/cli"
  sh "popper run -f {}"
}}}}
"""
    },
    # ##########################################################3
    "gitlab": {
        ".gitlab-ci.yml": """
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
  script: popper run -f {}
"""
    },
    # ##########################################################3
    "brigade": {
        "brigade.js": """
const { events, Job } = require("brigadier")
events.on("push", () => {
    var popper = new Job("popper", "python:3.7-slim-stretch")
    popper.tasks = [
        "apt-get update",
        "apt-get install -y git",
        "git clone https://github.com/systemslab/popper /tmp/popper",
        "export PYTHONUNBUFFERED=1",
        "pip install /tmp/popper/cli",
        "popper run -f {}"
    ]
    popper.run()
})
"""
    },
}


@click.command("ci", short_help="Generate CI service configuration files.")
@click.argument(
    "service",
    type=click.Choice(["travis", "circle", "jenkins", "gitlab", "brigade"]),
    required=True,
)
@click.option("-f", "--file", help="Specify workflow to run in CI.", required=True)
@pass_context
def cli(ctx, service, file):
    """Generates configuration files for distinct CI services. This command
    needs to be executed on the root of your Git repository folder.
    """
    if not os.path.exists(".git"):
        log.fail(
            "This command needs to be executed on the root of your "
            "Git project folder (where the .git/ folder is located)."
        )

    for ci_file, ci_file_content in ci_files[service].items():
        ci_file = os.path.join(os.getcwd(), ci_file)
        os.makedirs(os.path.dirname(ci_file), exist_ok=True)
        with open(ci_file, "w") as f:
            f.write(ci_file_content.format(file))

    log.info(f"Wrote {service} configuration successfully.")
