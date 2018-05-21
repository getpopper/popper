#!/usr/bin/env python

import click
import os
import requests
import subprocess
import base64
import json
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
@click.option(
    '--no-publish',
    is_flag=True,
    help='Just upload the record without publishing.',
    required=False,
)
@pass_context
def cli(ctx, service, key, no_publish):
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

    if service == 'zenodo':
        service_url = 'https://zenodo.org/api/deposit/depositions'
        params = {'access_token': key}

    if no_publish:
        archive_file = create_archive(project_root, project_name)
        deposition_id = upload_snapshot(service_url, params, archive_file)
        delete_archive(project_root, archive_file)

    else:
        # Get the list of depositions
        uploads = requests.get(service_url, params=params)

        if uploads.status_code == 200:
            if not uploads.json()[0]['submitted']:
                deposition_id = uploads.json()[0]['id']
            else:
                archive_file = create_archive(project_root, project_name)
                deposition_id = upload_snapshot(
                    service_url, params, archive_file
                )
                delete_archive(project_root, archive_file)

            metadata_url = service_url + '/{}'.format(deposition_id)
            publish_url = add_metadata(metadata_url, params)
            doi = publish_snapshot(publish_url, params)

    pu.info("Done..!")


def create_archive(project_root, project_name):
    """Creates a git archive of the popperized repository and returns the
    filename."""
    pu.info("Creating the archive...")
    os.chdir(project_root)
    archive_file = project_name + '.tar.gz'
    command = 'git archive master | gzip > ' + archive_file
    subprocess.call(command, shell=True)
    return archive_file


def upload_snapshot(service_url, params, filename):
    """Receives the service_url and the required paramters and the filename to
    be uploaded and uploads the deposit, but the deposit is not published
    at this step. Returns the deposition id."""
    # Create the deposit
    pu.info("Uploading the snapshot...")
    headers = {'Content-Type': "application/json"}
    r = requests.post(service_url, params=params, json={}, headers=headers)

    if r.status_code == 401:
        pu.fail("Your access token is invalid. "
                "Please enter a valid access token.")

    deposition_id = r.json()['id']
    upload_url = service_url + '/{}/files'.format(deposition_id)
    files = {'file': open(filename, 'rb')}
    data = {'filename': filename}

    # Upload the file
    r = requests.post(upload_url, data=data, files=files, params=params)
    response = {'status_code': r.status_code}
    if r.status_code == 201:
        file_id = r.json()['id']
        response['deposition_id'] = deposition_id
        pu.info(
            "Snapshot has been successfully uploaded. Your deposition id is "
            "{} and the file id is {}.".format(deposition_id, file_id)
        )
    else:
        pu.fail(
            "Status {}: Failed to upload your snapshot. Please "
            "try again.".format(r.status_code)
        )

    return deposition_id


def add_metadata(metadata_url, params):
    """Receives the metadata_url and other parameters, reads the metadata and
    adds that to the deposit. Returns the publish_url."""
    data = {
        'metadata': {
            'title': "This is the title",
            'upload_type': 'software',
            'description': "A suitable description",
            'creators': [
                {'name': 'Doe, John', 'affiliation': 'popper'},
            ]
        }
    }
    metadata_added = requests.put(
        metadata_url,
        params=params,
        data=json.dumps(data),
        headers={'Content-Type': 'application/json'}
    )
    if metadata_added.status_code == 200:
        return metadata_added.json()['links']['publish']  # publish_url
    else:
        pu.fail("Invalid metadata. Metadata could not be added successfully.")


def publish_snapshot(publish_url, params):
    """Publishes the snapshot to the provided publish_url and returns the DOI.
    """
    pu.info("Publishing the snapshot...")
    published = requests.post(publish_url, params=params)
    if published.status_code == 202:
        doi = published.json()['doi']
        doi_url = published.json()['doi_url']
        pu.info(
            "Snapshot has been successfully published with DOI "
            "{} and the DOI URL {}".format(doi, doi_url)
        )
    else:
        pu.fail(
            "Status {}: Could not publish the snapshot. "
            "Try again later.".format(published.status_code)
        )

    return doi_url


def delete_archive(project_root, archive_file):
    """Deletes the specified archive from the filesystem."""
    pu.info("Deleting the archive...")
    os.chdir(project_root)
    command = 'rm ' + archive_file
    subprocess.call(command, shell=True)


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
