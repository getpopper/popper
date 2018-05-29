#!/usr/bin/env python

import click
import os
import requests
import subprocess
import pyaes
import hashlib
import json
import popper.utils as pu

from popper.cli import pass_context


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
        try:
            key = os.environ['POPPER_ZENODO_API_TOKEN']
        except KeyError:
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
            try:
                if not uploads.json()[0]['submitted']:
                    deposition_id = uploads.json()[0]['id']
                else:
                    raise IndexError(
                        'No previous uploads exist or '
                        'previous upload is submitted.'
                    )
            except IndexError:
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
            "Status {}: Failed to upload your snapshot. "
            "Please try again.".format(published.status_code)
        )

    return deposition_id


def add_metadata(metadata_url, params):
    """Receives the metadata_url and other parameters, reads the metadata and
    adds that to the deposit. Returns the publish_url."""

    # Get the metadata from the .popper.yml file
    data = pu.read_config()['metadata']

    required_data = ['title', 'upload_type', 'abstract', 'author1']
    metadata_is_valid = True

    for req in required_data:
        if req not in data:
            metadata_is_valid = False
            break

    if not metadata_is_valid:
        pu.fail(
            "Metadata is not defined properly in .popper.yml. "
            "See the documentation for proper metadata format."
        )

    # Change abstract to description, if present
    data['description'] = '<p>' + data['abstract'] + '</p>'
    del data['abstract']

    # Collect the authors in a sorted manner
    creators = []
    for key in sorted(list(data.keys())):
        if 'author' in key:
            name, email, affiliation = map(
                lambda x: x.strip(), data[key].split(',')
            )
            if len(name.split()) == 2:
                name = ', '.join(name.split()[::-1])
            creators.append({'name': name, 'affiliation': affiliation})
            del data[key]
    data['creators'] = creators

    # Change the keywords to a list from string of comma separated values
    if 'keywords' in data:
        data['keywords'] = list(
            map(lambda x: x.strip(), data['keywords'].split(','))
        )

    data = {'metadata': data}

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
