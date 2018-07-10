#!/usr/bin/env python

import click
import popper.utils as pu


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


@click.command('service',
               short_help='Generates markdown for service badges')
@click.argument('service', required=False)
def cli(service):
    """Generates markdown for the badge of a service. Currently available
    services are: CloudLab, Chameleon, Google Cloud Engine and Popper.
    """
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

    pu.info('To add the "{}" badge to your readme, put this markdown inside '
            'your readme file:\n'.format(name))

    pu.info(markup)
