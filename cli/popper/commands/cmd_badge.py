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
    )
}


@click.command('service',
               short_help='Generates markdown for a "service ready" badge')
@click.argument('service', required=False)
def cli(service):
    if service is None or service not in services:
        pu.info('Available services:')
        for s in services:
            pu.info(' - {}'.format(s))

        if service is None:
            pu.fail('Please specify a service')
        else:
            pu.fail('Unknown service')

    markup = '[![{}]({})]({})'.format(*services[service])

    name, _, _ = services[service]

    pu.info('To add the "{}" badge to your readme, put this markdown inside '
            'your readme file:\n'.format(name))

    pu.info(markup)
