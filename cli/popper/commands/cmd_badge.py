#!/usr/bin/env python

import click
import requests
import popper.utils as pu

from popper.cli import pass_context
from popper.exceptions import BadArgumentUsage


services = {
    'cloudlab': (
        'CloudLab ready pipeline',
        'https://img.shields.io/badge/CloudLab-ready-blue.svg',
        'https://popper.readthedocs.io/en/docs-reorg/sections/examples.html#on'
        '-cloudlab-using-geni-lib'
    ),
    'chameleon': (
        'Chameleon ready pipeline',
        'https://img.shields.io/badge/Chameleon-ready-blue.svg',
        'https://popper.readthedocs.io/en/docs-reorg/sections/examples.html#on'
        '-chameleon-using-enos'
    ),
    'gce': (
        'Google Cloud Engine ready pipeline',
        'https://img.shields.io/badge/GCE-ready-blue.svg',
        'https://popper.readthedocs.io/en/docs-reorg/sections/examples.html#on'
        '-ec2-gce-using-terraform'
    ),
    'popper': (
        'Popper Status',
        'http://badges.falsifiable.us/{}/{}',
        'http://popper.rtfd.io/en/latest/sections/badge_server.html'
    )
}


@click.command('badge', short_help='Generates markdown for service badges')
@click.option(
    '--service',
    help='Name of the service for which badge is required',
    required=False,
)
@click.option(
    '--history',
    help='Get the history of badges generated for popper',
    required=False,
    is_flag=True
)
@pass_context
def cli(ctx, service, history):
    """Generates markdown for the badge of a service. Currently available
    services are: CloudLab, Chameleon, Google Cloud Engine and Popper. Both
    --service and --history cannot be used together, but one of them
    is required.
    """
    if (history and service) or (not history and not service):
        raise BadArgumentUsage(
            "--history and --service flags can't be used "
            "together.\nSee help for more info."
        )
    elif not history:
        if service is None or service not in services:
            if service is None:
                pu.fail('Please specify a service')
            else:
                pu.fail('Unknown service')

            pu.info('Available services:')
            for s in services:
                pu.info(' - {}'.format(s))

        if service == 'popper':
            remote_url = pu.get_remote_url()
            if not remote_url:
                pu.fail("Failed to fetch remote url for git repository")
            org, repo = remote_url.split('/')[-2:]
            markup = '[![{}]({})]({})'.format(
                services[service][0],
                services[service][1].format(org, repo),
                services[service][2]
            )
        else:
            markup = '[![{}]({})]({})'.format(*services[service])

        name, _, _ = services[service]
        pu.info('To add the "{}" badge to your readme, put this markdown '
                'inside your readme file:\n'.format(name))
        pu.info(markup)

    else:
        baseurl = pu.read_config().get(
            'badge-server-url', 'http://badges.falsifiable.us'
        )
        remote_url = pu.get_remote_url()
        if not remote_url:
            pu.fail("Failed to fetch remote url for git repository")
        org, repo = remote_url.split('/')[-2:]
        try:
            r = requests.get('{}/{}/{}/list'.format(baseurl, org, repo))
            if len(r.json()) == 0:
                pu.info("No records to show")
            else:
                pu.print_yaml(r.json())
        except requests.exceptions.RequestException:
            pu.fail("Could not communicate with the badge server")
