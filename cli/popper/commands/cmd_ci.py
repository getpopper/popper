import click
import os
import popper.utils as pu

from popper.cli import pass_context

ci_files = {
    'travis': {
        './.travis.yml': """
---
language: python
python: 2.7
services: docker
install:
- git clone https://github.com/systemslab/popper /tmp/popper
- pip install /tmp/popper
script: popper run
"""
    }
}


@click.command('ci', short_help='Generate CI service configuration files.')
@click.option(
    '--service',
    help='Name of CI service for which config files get generated.',
    type=click.Choice(['travis', 'circle', 'jenkins']),
    required=True
)
@pass_context
def cli(ctx, service):
    """Generates configuration files for distinct CI services.
    """
    project_root = pu.get_project_root()

    if service not in ci_files:
        pu.fail("Unrecognized service " + service)

    for ci_file, ci_file_content in ci_files[service].iteritems():
        ci_file = os.path.join(project_root, ci_file)
        # create parent folder
        if not os.path.isdir(os.path.dirname(ci_file)):
            os.makedirs(os.path.dirname(ci_file))

        # write content
        with open(ci_file, 'w') as f:
            f.write(ci_file_content)
