#!/usr/bin/env python

import os
import click
import requests
import popper.utils as pu
import sys

from popper.cli import pass_context
from popper.exceptions import BadArgumentUsage
from errno import ENOENT


services = {
    'cloudlab': (
        'CloudLab ready pipeline',
        'https://img.shields.io/badge/CloudLab-ready-blue.svg',
        'https://popper.readthedocs.io/en/docs-reorg/sections/examples.html#on-cloudlab-using-geni-lib'
    ),
    'chameleon': (
        'Chameleon ready pipeline',
        'https://img.shields.io/badge/Chameleon-ready-blue.svg',
        'https://popper.readthedocs.io/en/docs-reorg/sections/examples.html#on-chameleon-using-enos'
    ),
    'gce': (
        'Google Cloud Engine ready pipeline',
        'https://img.shields.io/badge/GCE-ready-blue.svg',
        'https://popper.readthedocs.io/en/docs-reorg/sections/examples.html#on-ec2-gce-using-terraform'
    ),
    'popper': (
        'Popper Status',
        'http://badges.falsifiable.us/{}/{}',
        'https://popper.rtfd.io/en/latest/sections/cli_features.html#popper-badges'
    )
}


@click.command('badge', short_help='Generates markdown text for badges')
@click.option(
    '--service',
    help='Name of the service for which badge is required',
    required=False,
)
@click.option(
    '--history',
    help=(
        'Get the history of badges generated for popper. '
        'Can\'t be used when --service is provided.'
    ),
    required=False,
    is_flag=True
)
@click.option(
    '--inplace',
    help=('Write markup for badge to the README.'),
    required=False,
    is_flag=True
)
@pass_context
def cli(ctx, service, history, inplace):
    """Generates markdown for the badge of a service. Currently available
    services are: CloudLab, Chameleon, Google Cloud Engine and Popper.
    """
    if history and service:
        raise BadArgumentUsage("--history can't be combined with other flags.")

    remote_url = pu.get_remote_url()

    if not remote_url:
        pu.fail("Failed to infer remote URL for git repository.")

    org, repo = remote_url.split('/')[-2:]

    if history:
        baseurl = pu.read_config().get('badge-server-url',
                                       'http://badges.falsifiable.us')
        try:
            r = requests.get('{}/{}/{}/list'.format(baseurl, org, repo))
            if r.json():
                pu.print_yaml(r.json())
            else:
                pu.info("No records to show")
        except requests.exceptions.RequestException:
            pu.fail("Could not communicate with the badge server")

        sys.exit(0)

    if not service and inplace:
        raise BadArgumentUsage("--inplace must be given with --service")

    if service is None:
        pu.fail('Please specify a service name.')
    if service not in services:
        pu.fail('Unknown service {}.'.format(service))

    if service == 'popper':
        org, repo = remote_url.split('/')[-2:]
        markup = '[![{}]({})]({})'.format(
            services[service][0],
            services[service][1].format(org, repo),
            services[service][2]
        )
    else:
        markup = '[![{}]({})]({})'.format(*services[service])

    if not inplace:
        pu.info(markup)
        sys.exit(0)

    try:
        os.chdir(pu.get_project_root())
        with open('README.md', 'r+') as f:
            content = f.read()
            f.seek(0, 0)
            f.write(markup + '\n\n' + content)
    except IOError as e:
        if e.errno == ENOENT:
            pu.fail(
                "README.md does not exist at the root of the project"
            )
