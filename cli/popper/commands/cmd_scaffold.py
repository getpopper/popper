import os

import click

from popper.cli import pass_context, log


@click.command('scaffold', short_help='Scaffolds a workflow folder.')
@pass_context
def cli(ctx):
    """Scaffolds a workflow.
    """
    curr_dir = os.getcwd()
    actions_dir = os.path.join(curr_dir, 'actions')

    main_workflow_content = """
workflow "example" {
  on = "push"
  resolves = "example action"
}

action "github official action" {
  uses = "actions/bin/sh@master"
  args = ["ls"]
}

action "docker action" {
  needs = "github official action"
  uses = "docker://node:6"
  args = ["node", "--version"]
}

action "example action" {
  needs = "docker action"
  uses = "./%s"
  args = ["github.com"]
}
"""

    dockerfile_content = """
FROM debian:stable-slim

LABEL "name"="curl"
LABEL "maintainer"="GitHub Actions <support+actions@github.com>"
LABEL "version"="1.0.0"

LABEL "com.github.actions.name"="cURL for GitHub Actions"
LABEL "com.github.actions.description"="Runs cURL in an Action"
LABEL "com.github.actions.icon"="upload-cloud"
LABEL "com.github.actions.color"="green"


COPY entrypoint.sh /entrypoint.sh

RUN apt-get update && \
    apt-get install curl -y && \
    apt-get clean -y

ENTRYPOINT ["sh", "/entrypoint.sh"]
"""

    entrypoint_content = """
#!/bin/sh
set -e

sh -c "curl $*"
"""

    readme = """
# An example Github Action
Executes cURL with arguments listed in the Action's args.
"""

    for filename in os.listdir(curr_dir):
        if filename.endswith('.workflow'):
            log.fail('.workflow file already present !')

    if not os.path.exists(actions_dir):
        os.mkdir(actions_dir)
        os.mkdir(os.path.join(actions_dir, 'example'))
    else:
        if not os.path.exists(os.path.join(actions_dir, 'example')):
            os.mkdir(os.path.join(actions_dir, 'example'))

    # Generate actions files
    with open(os.path.join(curr_dir, 'main.workflow'), 'w') as f:
        f.write(main_workflow_content % os.path.relpath(
            os.path.join(actions_dir, 'example'), curr_dir)
        )

    with open(os.path.join(actions_dir, 'example/Dockerfile'), 'w') as df:
        df.write(dockerfile_content)

    with open(os.path.join(actions_dir, 'example/entrypoint.sh'), 'w') as ef:
        ef.write(entrypoint_content)

    with open(os.path.join(actions_dir, 'example/README.md'), 'w') as rf:
        rf.write(readme)

    log.info('Successfully generated a workflow scaffold.')
