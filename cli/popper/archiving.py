# -*- coding: utf-8 -*-

import requests
import json
import os
import subprocess
import popper.utils as pu

from datetime import date


class BaseService():
    """Abstract class for archving services.

    Attributes:
        baseurl (str): Baseurl for the specific service
        params (dict): Parameters that need to be sent with the request
        deposition (dict): The last modified deposition, obtained from the
            service
    """

    baseurl = ''
    params = None
    deposition = None

    def __init__(self, access_token):
        """The __init__ method is responsible for getting the previous
        deposition from the service url, using the OAuth access token.
        It is meant to be overridden by the derived class.

        Args:
            access_token (str): OAuth token for the service
        """
        raise NotImplementedError(
            "This method is required to be implemented in the base class."
        )

    def is_last_deposition_published(self):
        """The method checks if the last modified/uploaded record is
        published or not. This will be overridden by the derived class.

        Returns:
            True if published, False if no deposition is uploaded or the last
            uploaded deposition is submitted.
        """
        raise NotImplementedError(
            "This method is required to be implemented in the base class."
        )

    def create_new_deposition(self):
        """This method creates a new deposition record. It will only
        be called when no previous deposition is found. This will be
        overridden by the derived class.

        Returns:
            The deposition id of the newly created record if successful,
             fails with proper message otherwise.
        """
        raise NotImplementedError(
            "This method is required to be implemented in the base class."
        )

    def create_new_version(self):
        """This method creates a new version of the last record. It will only
        be called when some previous deposition is found. This will be
        overridden by the derived class.

        Returns:
            The deposition id of the newly created version if successful,
             fails with proper message otherwise.
        """
        raise NotImplementedError(
            "This method is required to be implemented in the base class."
        )

    def delete_previous_file(self):
        """This method deletes the previously uploaded file so that new file
        can be uploaded for the newer version. This method will only be called
        when previous record exists.
        """
        raise NotImplementedError(
            "This method is required to be implemented in the base class."
        )

    def upload_new_file(self, deposition_id):
        """This method uploads a new file to a record.

        Args:
            deposition_id (str): Deposition id of the record to which the
                new file will be uploaded
        """
        raise NotImplementedError(
            "This method is required to be implemented in the base class."
        )

    def create_new_draft(self):
        """This method creates a new draft record if the previously modified/
        uploaded record is published, or updates it, if it is unpublished.
        The updation includes files and metadata.
        """
        raise NotImplementedError(
            "This method is required to be implemented in the base class."
        )

    def publish_last_unsubmitted(self):
        """This method publishes the last unpublished record and stores the doi
        in the .popper.yml file.
        """
        raise NotImplementedError(
            "This method is required to be implemented in the base class."
        )

    def create_archive(self):
        """Creates an archive of the entire repsitory
        using the git archive command.

        Returns:
            Name of the archive file.
        """
        project_root = pu.get_project_root()
        project_name = os.path.basename(project_root)
        os.chdir(project_root)
        archive_file = project_name + '.tar.gz'
        command = 'git archive master | gzip > ' + archive_file
        subprocess.call(command, shell=True)
        return archive_file

    def delete_archive(self):
        """Deletes the created archive from the filesystem.
        """
        project_root = pu.get_project_root()
        archive_file = os.path.basename(project_root) + '.tar.gz'
        os.chdir(project_root)
        command = 'rm ' + archive_file
        subprocess.call(command, shell=True)


class Zenodo(BaseService):

    def __init__(self, access_token):
        self.baseurl = 'https://zenodo.org/api/deposit/depositions'
        self.params = {'access_token': access_token}
        r = requests.get(self.baseurl, params=self.params)
        try:
            self.deposition = r.json()[0]
        except IndexError:
            self.deposition = None
        except KeyError:
            if r.status_code == 401:
                pu.fail(
                    "The access token provided was invalid. "
                    "Please provide a valid access_token"
                )
            else:
                pu.fail(
                    "Status {}: Could not fetch the depositions."
                    "Try again later.".format(r.status_code)
                )

    def _is_last_deposition_published(self):
        if self.deposition is None:
            return False
        else:
            return self.deposition['submitted']

    def create_new_deposition(self):
        url = self.baseurl
        headers = {"Content-Type": "application/json"}
        r = requests.post(url, params=self.params, json={}, headers=headers)
        if r.status_code == 201:
            return r.json()['id']
        else:
            pu.fail(
                "Status {}: Could not create new deposition."
                .format(r.status_code)
            )

    def create_new_version(self):
        deposition_id = self.deposition['id']
        url = '{}/{}/actions/newversion'.format(self.baseurl, deposition_id)
        r = requests.post(url, params=self.params)
        if r.status_code == 201:
            return r.json()['id']
        else:
            pu.fail(
                "Status {}: Could not create a new version of your deposition."
                .format(r.status_code)
            )

    def update_metadata_from_yaml(self, deposition_id):
        """Reads required metatdata from .popper.yml and updates the
        metadata for the record. This will only be called when no previous
        deposition is found.

        Args:
            deposition_id (str): The deposition id whose metadata will
                be updated
        """
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
        url = '{}/{}'.format(self.baseurl, deposition_id)
        r = requests.put(
            url, data=json.dumps(data), params=self.params,
            headers={'Content-Type': "application/json"}
        )
        if r.status_code != 200:
            pu.fail(
                "Status {}: Failed to update metadata.".format(r.status_code)
            )

    def update_metadata(self):
        """Reads required metatdata from the previous record and updates it
        from .popper.yml. The record is updated with the new data. This will
        only be called when some previous deposition is found.
        """
        data = self.deposition['metadata']
        config = pu.read_config()['metadata']

        try:
            data['description'] = '<p>{}</p>'.format(config['abstract'])
            data['title'] = config['title']
            data['publication_date'] = str(date.today())
            data['keywords'] = list(
                map(lambda x: x.strip(), config['keywords'].split(','))
            )
            creators = []
            for key in sorted(list(config.keys())):
                if 'author' in key:
                    name, email, affiliation = map(
                        lambda x: x.strip(), config[key].split(',')
                    )
                    if len(name.split()) == 2:
                        name = ', '.join(name.split()[::-1])
                    creators.append({'name': name, 'affiliation': affiliation})
            data['creators'] = creators
        except KeyError:
            pu.fail(
                "Metadata is not defined properly in .popper.yml. "
                "See the documentation for proper metadata format."
            )

        data = {'metadata': data}
        url = '{}/{}'.format(self.baseurl, self.deposition['id'])
        r = requests.put(
            url, data=json.dumps(data), params=self.params,
            headers={'Content-Type': "application/json"}
        )
        if r.status_code != 200:
            pu.fail(
                "Status {}: Failed to update metadata.".format(r.status_code)
            )

    def delete_previous_file(self):
        deposition_id = self.deposition['id']
        url = '{}/{}/files'.format(self.baseurl, self.deposition['id'])
        r = requests.get(url, params=self.params)
        if r.status_code == 200:
            old_file_id = r.json()[0]['id']
        else:
            pu.fail(
                "Status {}: Failed to get the files of the previous version."
                .format(r.status_code)
            )

        url = '{}/{}/files/{}'.format(self.baseurl, deposition_id, old_file_id)
        r = requests.delete(url, params=self.params)
        if r.status_code != 201:
            pu.fail(
                "Status {}: Failed to delete files of the previous version."
                .format(r.status_code)
            )

    def upload_new_file(self, deposition_id):
        new_file = self.create_archive()
        project_root = pu.get_project_root()
        url = '{}/{}/files'.format(self.baseurl, deposition_id)
        data = {'filename': new_file}
        files = {'file': open(os.path.join(project_root, new_file), 'rb')}
        r = requests.post(url, data=data, files=files, params=self.params)
        if r.status_code != 201:
            pu.fail(
                "Status {}: Failed to upload a new snapshot."
                .format(r.status_code)
            )

    def create_new_draft(self):
        if self.deposition is None:
            deposition_id = self.create_new_deposition()
            self.update_metadata_from_yaml(deposition_id)
        else:
            if self.is_last_deposition_published():
                deposition_id = self.create_new_version()
            else:
                deposition_id = self.deposition['id']
            self.delete_previous_file()
            self.update_metadata()

        self.upload_new_file(deposition_id)

    def publish_last_unsubmitted(self):
        r = requests.get(self.baseurl, params=self.params)
        config = pu.read_config()
        try:
            deposition_id = r.json()[0]['id']
        except (KeyError, IndexError):
            pu.fail("No previously unpublished records exist.")

        url = '{}/{}/actions/publish'.format(self.baseurl, deposition_id)
        r = requests.post(url, params=self.params)
        if r.status_code == 202:
            doi = r.json()['doi']
            doi_url = r.json()['doi_url']
            pu.info(
                "Snapshot has been successfully published with DOI "
                "{} and the DOI URL {}".format(doi, doi_url)
            )
            config['metadata']['zenodo_doi'] = doi
            config['metadata']['zenodo_doi_url'] = doi_url
            pu.write_config(config)
        else:
            pu.fail(
                "Status {}: Failed to publish the record."
                .format(r.status_code)
            )
