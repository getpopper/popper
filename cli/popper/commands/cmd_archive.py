#!/usr/bin/env python

import click
import os
import pyaes
import hashlib
import popper.utils as pu
import sys

from popper.archiving import Zenodo, Figshare
from popper.cli import pass_context


@click.command('archive',
               short_help='Archive and publish a snapshot of the repository.')
@click.option(
    '--service',
    help='Name of the archiving service.',
    required=True,
)
@click.option(
    '--publish',
    help='Publish the archive and obtain a DOI.',
    default=False,
    is_flag=True,
)
@click.option(
    '--ignore-untracked',
    help='Ignore files not tracked by Git.',
    default=False,
    is_flag=True,
)
@click.option(
    '--key',
    help='Access token for your service.',
    required=False,
)
@click.option(
    '--show-doi',
    help='Show the DOI, URL for the record and exit.',
    default=False,
    is_flag=True,
)
@pass_context
def cli(ctx, service, publish, ignore_untracked, key, show_doi):
    """Creates and uploads a snapshot of the project to an archival
    service (currently supports Zenodo and Figshare). This command relies on
    having an account on the underlying service, as well as providing an API
    token. See http://bit.ly/popper-docs-arx-doi for instructions on how to
    generate tokens.

    When this command executes, a terminal prompt is shown so you can provide
    the token for the underlying service. Alternatively, this command looks for
    a POPPER_<SERVICE>_API_TOKEN environment variable (where <SERVICE> is the
    name of the service, e.g. POPPER_ZENODO_API_TOKEN) and, if found, it uses
    it to authenticate without prompting the user for the token.

    All files contained in the project folder are included in the snapshot. The
    --ignore-untracked causes the command to include only files that are
    tracked by Git.

    By default, the command only uploads a snapshot of the current folder. If
    the --publish flag is given, in addition to uploading the snapshot, the
    archive is published and a DOI is obtained from the underlying service. The
    DOI as well as the URL to the archive on the service web site are printed.
    If --show-doi is given, the DOI and URL of record is shown. The printed URL
    will not be functional unless the record has been published.
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

    if show_doi and publish:
        pu.fail("--show-doi can not be given along with --publish")

    archive = services[service](key)

    pu.info('Looking for an existing record for the project.')
    archive.fetch_depositions()

    if show_doi:
        if archive.record_exists():
            pu.info('Found record for project: {}'.format(archive.record_id))
            archive.show_doi()
        else:
            pu.info('No record for project exists.')
        sys.exit(0)

    if not archive.record_exists():
        pu.info('No record exists yet; creating one for project.')
        archive.create_new_deposition()
        pu.info('Record ID: {}'.format(archive.record_id))
    else:
        pu.info('Record exists: {}'.format(archive.record_id))

        if archive.is_last_deposition_published():
            pu.info('A published version exists, creating new version.')
            archive.create_new_version()
        else:
            pu.info('An unpublished version exists, updating it.')

        archive.delete_previous_file()

    archive.ignore_untracked = ignore_untracked

    pu.info('Uploading files.')
    archive.upload_snapshot()

    if publish:
        pu.info('Publishing record and obtaining DOI.')
        archive.publish_snapshot()
        archive.show_doi()

    pu.info("Done!")


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
