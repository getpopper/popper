# -*- coding: utf-8 -*-

import requests
import json
import os
import hashlib
import subprocess
import popper.utils as pu
import sys

from datetime import date


class BaseService(object):
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
    ignore_untracked = False

    def __init__(self):
        """The __init__ method of the base class is responsible for checking
        if there are no unstaged changes in the repository and fail otherwise.

        The __init__ method of the derived classes should call this method
        using the super function. The __init__ method of the derived class,
        however, is responsible for getting the previous relevant deposition
        from the service url, using the OAuth access token.
        """
        remote_url = pu.get_remote_url()
        if not remote_url:
            pu.fail("Failed to fetch remote url for git repository.")

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

    def upload_snapshot(self):
        """This method creates a new record if there no previously uploaded
        record exists, or creates a new version if it does. The files and
        metadata are updated.
        """
        raise NotImplementedError(
            "This method is required to be implemented in the base class."
        )

    def publish_snapshot(self):
        """This method publishes an archive and obtains a DOI for it by using
        the underlying service. The DOI is stored in the .popper.yml file.
        """
        raise NotImplementedError(
            "This method is required to be implemented in the base class."
        )

    def create_archive(self):
        """Creates an archive of the entire project folder using gzip or zip.

        Returns:
            Name of the archive file.
        """
        cwd = os.getcwd()
        project_root = pu.get_project_root()
        project_name = os.path.basename(project_root)
        os.chdir(project_root)

        pu.info('Creating archive file')
        archive_file = project_name + '.tar'
        cmd = 'git archive master > ' + archive_file
        subprocess.check_output(cmd, shell=True)

        if not self.ignore_untracked:
            cmd = (
                'git ls-files --others --exclude-standard -z | '
                'xargs -0 tar rf ' + archive_file
            )
            subprocess.check_output(cmd, shell=True)

        cmd = 'gzip ' + archive_file
        subprocess.check_output(cmd, shell=True)

        os.chdir(cwd)

        return '/tmp/' + archive_file + '.gz'

    def delete_archive(self):
        """Deletes the created archive from the filesystem.
        """
        cwd = os.getcwd()
        project_root = pu.get_project_root()
        archive_file = '/tmp/' + os.path.basename(project_root) + '.tar'
        os.chdir(project_root)
        cmd = 'rm ' + archive_file
        subprocess.call(cmd, shell=True)
        cmd = 'rm ' + archive_file + '.gz'
        subprocess.call(cmd, shell=True)
        os.chdir(cwd)


class Zenodo(BaseService):

    def __init__(self, access_token):
        super(Zenodo, self).__init__()
        self.baseurl = 'https://zenodo.org/api/deposit/depositions'
        self.params = {'access_token': access_token}
        r = requests.get(self.baseurl, params=self.params)
        try:
            depositions = r.json()
            pu.info('existing depositions:\n', r.json())
            sys.exit(0)
            remote_url = pu.get_remote_url()
            for deposition in depositions:
                metadata = deposition['metadata']
                try:
                    identifiers = metadata['related_identifiers']
                    if identifiers[0]['identifier'] == remote_url:
                        self.deposition = deposition
                except KeyError:
                    pass
        except TypeError:
            if r.status_code == 401:
                pu.fail("The access token provided was invalid.")
            else:
                pu.fail("Error {}: {}".format(r.status_code, r.json()))

    def is_last_deposition_published(self):
        if self.deposition is None:
            return False
        else:
            return self.deposition['submitted']

    def create_new_deposition(self):
        url = self.baseurl
        headers = {"Content-Type": "application/json"}
        r = requests.post(url, params=self.params, json={}, headers=headers)
        if r.status_code == 201:
            self.deposition = r.json()
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
            url = self.baseurl
            r = requests.get(url, params=self.params)
            try:
                self.deposition = r.json()[0]
            except IndexError:
                pu.fail(
                    "Status {}: Could not fetch the depositions."
                    "Try again later.".format(r.status_code)
                )
        else:
            pu.fail(
                "Status {}: Could not create a new version of your deposition."
                .format(r.status_code)
            )

    def update_metadata_from_yaml(self):
        """Reads required metatdata from .popper.yml and updates the
        metadata for the record. This will only be called when no previous
        deposition is found.

        Args:
            deposition_id (str): The deposition id whose metadata will
                be updated
        """
        deposition_id = self.deposition['id']
        config = pu.read_config()['metadata']
        data = {}
        required_data = ['title', 'upload_type', 'abstract', 'author1']
        metadata_is_valid = True

        for req in required_data:
            if req not in config:
                metadata_is_valid = False
                break

        if not metadata_is_valid:
            pu.fail(
                "Metadata is not defined properly in .popper.yml. "
                "See the documentation for proper metadata format."
            )

        data['title'] = config['title']

        # Change abstract to description, if present
        data['description'] = '<p>' + config['abstract'] + '</p>'

        # Collect the authors in a sorted manner
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

        # Change the keywords to a list from string of comma separated values
        if 'keywords' in config:
            data['keywords'] = list(
                map(lambda x: x.strip(), config['keywords'].split(','))
            )

        data['related_identifiers'] = [{
            "identifier": pu.get_remote_url(),
            "relation": "isSupplementTo",
            "scheme": "url"
        }]

        data['upload_type'] = config['upload_type']
        if config['upload_type'] == 'publication':
            data['publication_type'] = config['publication_type']

        pu.info('Updating metadata.')
        data = {'metadata': data}
        url = '{}/{}'.format(self.baseurl, deposition_id)
        r = requests.put(
            url, data=json.dumps(data), params=self.params,
            headers={'Content-Type': "application/json"}
        )
        if r.status_code != 200:
            pu.fail("{} - Failed to update metadata: {}".format(r.status_code,
                                                                r.json()))
        pu.info('Successfully updated metadata.')

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
            try:
                old_file_id = r.json()[0]['id']
                url = '{}/{}/files/{}'.format(
                    self.baseurl, deposition_id, old_file_id
                )
                r = requests.delete(url, params=self.params)
                if r.status_code != 204:
                    pu.fail(
                        "Status {}: Failed to delete files of the "
                        "previous version.".format(r.status_code)
                    )
            except IndexError:
                pass
        else:
            pu.fail(
                "Status {}: Failed to get the files of the previous version."
                .format(r.status_code)
            )

    def upload_new_file(self):
        pu.info('Uploading files.')
        deposition_id = self.deposition['id']
        new_file = self.create_archive()
        project_root = pu.get_project_root()
        url = '{}/{}/files'.format(self.baseurl, deposition_id)
        data = {'filename': new_file}
        files = {'file': open(os.path.join(project_root, new_file), 'rb')}
        self.delete_archive()
        r = requests.post(url, data=data, files=files, params=self.params)
        if r.status_code != 201:
            pu.fail(
                "Status {}: Failed to upload a new snapshot."
                .format(r.status_code)
            )

    def upload_snapshot(self):
        if self.deposition is None:
            self.create_new_deposition()
            self.update_metadata_from_yaml()
        else:
            if self.is_last_deposition_published():
                self.create_new_version()
            self.delete_previous_file()
            self.update_metadata()

        self.upload_new_file()

    def publish_snapshot(self):
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


class Figshare(BaseService):

    def __init__(self, access_token):
        super(Figshare, self).__init__()
        self.baseurl = 'https://api.figshare.com/v2/account/articles'
        self.params = {'access_token': access_token}
        r = requests.get(self.baseurl, params=self.params)
        if r.status_code == 200:
            depositions = r.json()
            remote_url = pu.get_remote_url()
            for deposition in depositions:
                deposition_id = deposition['id']
                url = '{}/{}'.format(self.baseurl, deposition_id)
                r = requests.get(url, params=self.params)
                deposition = r.json()
                if remote_url in deposition['references']:
                    self.deposition = deposition
                    break
        elif r.status_code == 403:
            pu.fail(
                "The access token provided was invalid. "
                "Please provide a valid access_token."
            )
        else:
            pu.fail(
                "Status {}: Could not fetch the depositions."
                "Try again later.".format(r.status_code)
            )

    def is_last_deposition_published(self):
        if self.deposition is None:
            return False
        else:
            return self.deposition['published_date'] is not None

    def create_new_deposition(self):
        url = self.baseurl
        data = {
            'title': pu.read_config()['metadata']['title']
        }
        r = requests.post(url, params=self.params, data=json.dumps(data))
        if r.status_code == 201:
            location = r.json()['location']
            r = requests.get(location, params=self.params)
            if r.status_code == 200:
                self.deposition = r.json()
            else:
                pu.fail(
                    "Status {}: Could not fetch the depositions."
                    "Try again later.".format(r.status_code)
                )
        else:
            pu.fail(
                "Status {}: Could not create new deposition."
                .format(r.status_code)
            )

    def create_new_version(self):
        """If the article is already published, and its files are modified,
        a new version is created instead of new deposition. So, there is no
        need to implement this method.
        """
        pass

    def update_metadata(self):
        """Reads required metatdata from .popper.yml and updates the
        metadata for the record. This will only be called when no previous
        deposition is found.

        Args:
            deposition_id (str): The deposition id whose metadata will
                be updated
        """
        deposition_id = self.deposition['id']
        config = pu.read_config()['metadata']
        data = {}
        required_data = ['title', 'abstract', 'categories', 'keywords']
        metadata_is_valid = True

        for req in required_data:
            if req not in config:
                metadata_is_valid = False
                break

        if not metadata_is_valid:
            pu.fail(
                "Metadata is not defined properly in .popper.yml. "
                "See the documentation for proper metadata format."
            )

        # Change abstract to description, if present
        data['description'] = config['abstract']

        # Collect the authors in a sorted manner
        authors = []
        for key in sorted(list(config.keys())):
            if 'author' in key:
                name, email, affiliation = map(
                    lambda x: x.strip(), config[key].split(',')
                )
                authors.append({'name': name})
        if len(authors) != 0:
            data['authors'] = authors

        # Change the keywords to a list from string of comma separated values
        data['tags'] = list(
            map(lambda x: x.strip(), config['keywords'].split(','))
        )

        categories = []
        try:
            categories.append(int(config['categories']))
        except ValueError:
            categories = list(
                map(lambda x: int(x.strip()), config['categories'].split(','))
            )
        data['categories'] = categories
        data['references'] = [pu.get_remote_url()]

        url = '{}/{}'.format(self.baseurl, deposition_id)
        r = requests.put(
            url, data=json.dumps(data), params=self.params
        )
        if r.status_code != 205:
            pu.fail(
                "Status {}: Failed to update metadata.".format(r.status_code)
            )

    def delete_previous_file(self):
        deposition_id = self.deposition['id']
        url = '{}/{}/files'.format(self.baseurl, deposition_id)
        r = requests.get(url, params=self.params)
        if r.status_code == 200:
            try:
                old_file_id = r.json()[0]['id']
                url = '{}/{}/files/{}'.format(
                    self.baseurl, deposition_id, old_file_id
                )
                r = requests.delete(url, params=self.params)
                if r.status_code != 204:
                    pu.fail(
                        "Status {}: Failed to delete files of the "
                        "previous version.".format(r.status_code)
                    )
            except IndexError:
                pass
        else:
            pu.fail(
                "Status {}: Failed to get the files of the previous version."
                .format(r.status_code)
            )

    def upload_new_file(self):
        new_file = self.create_archive()
        project_root = pu.get_project_root()
        file_name = os.path.join(project_root, new_file)
        CHUNK_SIZE = 1048576
        # Initiate file upload
        with open(file_name, 'rb') as stream:
            md5 = hashlib.md5()
            size = 0
            data = stream.read(CHUNK_SIZE)
            while data:
                size += len(data)
                md5.update(data)
                data = stream.read(CHUNK_SIZE)
        md5, size = md5.hexdigest(), size
        data = {
            'name': new_file,
            'md5': md5,
            'size': size
        }
        deposition_id = self.deposition['id']
        url = '{}/{}/files'.format(
            self.baseurl, deposition_id
        )
        r = requests.post(url, data=json.dumps(data), params=self.params)

        # Receive the location and issue a get request
        location = r.json()['location']
        r = requests.get(location, params=self.params)

        # Receive the upload url and issue a get request to the upload url
        # to receive the number of file parts
        file_info = r.json()
        url = file_info['upload_url']
        r = requests.get(url, params=self.params)

        # Upload all the file parts
        parts = r.json()['parts']
        with open(file_name, 'rb') as stream:
            for part in parts:
                upload_data = file_info.copy()
                upload_data.update(part)
                url = '{upload_url}/{partNo}'.format(**upload_data)

                stream.seek(part['startOffset'])
                data = stream.read(part['endOffset'] - part['startOffset'] + 1)

                r = requests.put(url, data=data, params=self.params)
                if r.status_code != 200:
                    self.delete_archive()
                    pu.fail(
                        "Status {}: Could not upload the file. Please"
                        "try again later.".format(r.status_code)
                    )

        self.delete_archive()

        # Complete the file upload
        url = '{}/{}/files/{}'.format(
            self.baseurl, deposition_id, file_info['id']
        )
        r = requests.post(url, params=self.params)
        if r.status_code != 202:
            pu.fail(
                "Status {}: Could not complete the file upload. Please"
                "try again later.".format(r.status_code)
            )

    def upload_snapshot(self):
        if self.deposition is None:
            self.create_new_deposition()
        else:
            if self.is_last_deposition_published():
                self.create_new_version()
            self.delete_previous_file()

        self.upload_new_file()
        self.update_metadata()

    def publish_snapshot(self):

        url = '{}/{}/publish'.format(
            self.baseurl, self.deposition['id']
        )
        r = requests.post(url, params=self.params)
        if r.status_code == 201:
            url = r.json()['location']
            r = requests.get(url, params=self.params)
            doi = r.json()['doi']
            doi_url = 'https://doi.org/{}'.format(doi)
            pu.info(
                "Snapshot has been successfully published with DOI "
                "{} and the DOI URL {}".format(doi, doi_url)
            )
            config = pu.read_config()
            config['metadata']['figshare_doi'] = doi
            config['metadata']['figshare_doi_url'] = doi_url
            pu.write_config(config)
        else:
            pu.fail(
                "Status {}: Failed to publish the record."
                .format(r.status_code)
            )
