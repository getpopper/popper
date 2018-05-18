#!/usr/bin/env python

import click
import os
import requests
import subprocess
import base64
import popper.utils as pu

from popper.cli import pass_context
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend


@click.command('archive', short_help='Create a snapshot of the repository.')
@click.argument('service', required=True)
@click.option(
    '--key',
    help='Access token for your service.',
    required=False,
)
@pass_context
def cli(ctx, service, key):
    """Creates a archive of the repository on the provided service using an
    access token. Reports an error if archive creation is not successful.
    Currently supported services are Zenodo.
    """
    supported_services = ['zenodo']

    if service not in supported_services:
        pu.fail("The service {} is not supported. See popper archive "
                "--help for more info.".format(service))

    project_root = pu.get_project_root()
    project_name = os.path.basename(project_root)

    if not key:
        key = get_access_token(service, project_root)

    # Create the archive
    os.chdir(project_root)
    archive_file = project_name + '.tar.gz'
    command = 'git archive master | gzip > ' + archive_file
    subprocess.call(command, shell=True)

    response = create_snapshot(service, key, archive_file)

    # Clean up a bit
    command = 'rm ' + archive_file
    subprocess.call(command, shell=True)

    if response['status_code'] == 201:
        pu.info(response['message'])
    else:
        pu.fail(response['message'])


def create_snapshot(service, access_token, filename):
    """Creates a deposit and uploads the archive to the requested service.
    Reports an error if access token is invalid.Returns appropriate response,
    if access token is valid.
    """
    if service == 'zenodo':
        service_url = 'https://zenodo.org/api/deposit/depositions'
        params = {'access_token': access_token}

        # Create the deposit
        headers = {'Content-Type': "application/json"}
        r = requests.post(service_url, params=params, json={}, headers=headers)

        if r.status_code == 401:
            pu.fail("Your access token is invalid. "
                    "Please enter a valid access token.")

        deposition_id = r.json()['id']
        service_url += '/{}/files'.format(deposition_id)
        files = {'file': open(filename, 'rb')}
        data = {'filename': filename}

        # Upload the file
        r = requests.post(service_url, data=data, files=files, params=params)

        response = {'status_code': r.status_code}
        if r.status_code == 201:
            file_id = r.json()['id']
            response['message'] = (
                "Snapshot has been successfully uploaded. Your deposition id"
                " is {} and the file id is {}.".format(deposition_id, file_id)
            )
        else:
            response['message'] = (
                "Failed to upload your snapshot. Please try again."
            )

        return response


def get_access_token(service, cwd):
    """Tries to read the access token from a key file. If not present,
    prompts the user for a key and also stores the key in a key file
    if the user wishes."""
    os.chdir(cwd)
    try:
        with open('.{}.key'.format(service), 'r') as keyfile:
            encrypted_access_token = keyfile.read().strip().encode()
            passphrase = click.prompt(
                'Please enter your passphrase for {}'.format(service),
                hide_input=True
            ).encode()
            f = Fernet(generate_key(passphrase))
            try:
                access_token = f.decrypt(encrypted_access_token).decode("utf8")
            except InvalidToken:
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
                'Enter a strong passphrase',
                hide_input=True
            ).encode()
            f = Fernet(generate_key(passphrase))
            encrypted_access_token = f.encrypt(access_token.encode())
            with open('.{}.key'.format(service), 'w') as keyfile:
                keyfile.writelines(encrypted_access_token.decode("utf8"))
                pu.info('Your key is stored in .{}.key'.format(service))

    return access_token


def generate_key(passphrase):
    """Helper function that takes the passphrase as a bytes object
    and returns a key suitable for encryption with Fernet."""
    digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
    digest.update(passphrase)
    return base64.urlsafe_b64encode(digest.finalize())
