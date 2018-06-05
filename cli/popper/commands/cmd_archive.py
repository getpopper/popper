#!/usr/bin/env python

import click
import os
import pyaes
import hashlib
import popper.utils as pu

from popper.archiving import Zenodo, Figshare
from popper.cli import pass_context


@click.command('archive', short_help='Create a snapshot of the repository.')
@click.option(
    '--service',
    help='Name of the archiving service.',
    required=True,
)
@click.option(
    '--key',
    help='Access token for your service.',
    required=False,
)
@pass_context
def cli(ctx, service, key):
    """Creates a archive of the repository on the provided service using an
    access token. Reports an error if archive creation is not successful.
    Currently supported services are Zenodo and Figshare.
    """
    services = {
        'zenodo': Zenodo,
        'figshare': Figshare
    }
    environment_variables = {
        'zenodo': 'POPPER_ZENODO_API_TOKEN',
        'figshare': 'POPPER_FIGSHARE_API_TOKEN'
    }

    if service not in services:
        pu.fail("The service {} is not supported. See popper archive "
                "--help for more info.".format(service))

    if not key:
        try:
            key = os.environ[environment_variables[service]]
        except KeyError:
            key = get_access_token(service)

    archive = services[service](key)
    archive.publish_snapshot()

    pu.info("Done..!")


def get_access_token(service):
    """Tries to read the access token from a key file. If not present,
    prompts the user for a key and also stores the key in a key file
    if the user wishes."""
    project_root = pu.get_project_root()
    os.chdir(project_root)
    try:
        with open('.{}.key'.format(service), 'r') as keyfile:
            encrypted_access_token = keyfile.read().strip()
            passphrase = click.prompt(
                'Please enter your passphrase for {}'.format(service),
                hide_input=True
            ).encode()
            aes = pyaes.AESModeOfOperationCTR(generate_key(passphrase))
            try:
                access_token = aes.decrypt(encrypted_access_token).decode()
            except UnicodeDecodeError:
                pu.fail(
                    "Invalid passphrase. Please use the same passphrase "
                    "used at the time of encrypting the access_token."
                )
    except FileNotFoundError:
        pu.info('No access token found for {}'.format(service))
        access_token = click.prompt('Please enter your access token for {}'
                                    .format(service))
        if click.confirm('Would you like to store this key?'):
            passphrase = click.prompt(
                'Enter a strong passphrase', hide_input=True
            ).encode()
            aes = pyaes.AESModeOfOperationCTR(generate_key(passphrase))
            encrypted_access_token = aes.encrypt(access_token)
            with open('.{}.key'.format(service), 'w') as keyfile:
                keyfile.writelines('{}'.format(
                    ''.join(chr(b) for b in encrypted_access_token)
                ))
                pu.info('Your key is stored in .{}.key'.format(service))

    return access_token


def generate_key(passphrase):
    """Helper function that takes the passphrase as a bytes object and returns
    a 8-bit key that can be used for encryption with DES algorithm."""
    digest = hashlib.sha256(passphrase).digest()
    return digest[:16]
