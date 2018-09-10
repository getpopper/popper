# -*- coding: utf-8 -*-

import requests
import json
import os
import hashlib
import subprocess
import popper.utils as pu

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
    record_id = 0
    ignore_untracked = False
    doi_prefix = ''
    doi_url_prefix = ''
    is_last_published = False
    remote_url = ''

    def __init__(self):
        """The __init__ method of the base class is responsible for checking
        if there are no unstaged changes in the repository and fail otherwise.

        The __init__ method of the derived classes should call this method
        using the super function. The __init__ method of the derived class,
        however, is responsible for getting the previous relevant deposition
        from the service url, using the OAuth access token.
        """
        self.remote_url = pu.get_remote_url()
        if not self.remote_url:
            pu.fail(
                "Failed to fetch remote url for git repository. The "
                "'archive' commands relies on having"
            )

    def fetch_depositions(self):
        """This method fetches depositions on the underlying service and looks
        for a record for this project.
        """
        raise NotImplementedError(
            "This method is required to be implemented in the base class."
        )

    def is_last_deposition_published(self):
        return self.is_last_published

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
        """This method creates an archive and uploads it.
        """
        raise NotImplementedError(
            "This method is required to be implemented in the base class."
        )

    def record_exists(self):
        """Whether a record exists for project.
        """
        return self.record_id != 0

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

        archive_file = '/tmp/' + project_name + '.tar'
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

        return archive_file + '.gz'

    def delete_archive(self):
        """Deletes the created archive from the filesystem.
        """
        cwd = os.getcwd()
        project_root = pu.get_project_root()
        archive_file = '/tmp/' + os.path.basename(project_root) + '.tar.gz'
        os.chdir(project_root)
        subprocess.call('rm ' + archive_file, shell=True)
        os.chdir(cwd)

    def show_doi(self):
        """If a published archive exists for the project, prints the DOI
        """
        pu.info('DOI: {}{}'.format(self.doi_prefix, self.record_id))
        pu.info('URL: {}{}'.format(self.doi_url_prefix, self.record_id))

        if not self.is_last_deposition_published():
            pu.info("NOTE: DOI URL won't work as no record has been published")


class Zenodo(BaseService):

    def __init__(self, access_token):
        super(Zenodo, self).__init__()

        self.baseurl = 'https://zenodo.org/api/deposit/depositions'
        self.params = {'access_token': access_token}
        self.doi_prefix = '10.5281/zenodo.'
        self.doi_url_prefix = 'https://doi.org/10.5281/zenodo.'

    def fetch_depositions(self):
        r = requests.get(self.baseurl, params=self.params)
        try:
            depositions = r.json()
            for deposition in depositions:
                metadata = deposition['metadata']
                if 'related_identifiers' not in metadata:
                    continue
                for identifier in metadata['related_identifiers']:
                    if identifier['identifier'] != self.remote_url:
                        continue
                    self.deposition = deposition
                    self.is_last_published = self.deposition['submitted']
                    self.record_id = self.deposition['id']
                    break

        except TypeError:
            if r.status_code == 401:
                pu.fail("The access token provided was invalid.")
            else:
                pu.fail("Error {}: {}".format(r.status_code, r.json()))

    def create_new_deposition(self):
        url = self.baseurl
        headers = {"Content-Type": "application/json"}
        r = requests.post(url, params=self.params, json={}, headers=headers)
        if r.status_code != 201:
            pu.fail("Status {}: {}".format(r.status_code, r.json()))
        self.deposition = r.json()
        self.record_id = self.deposition['id']

    def create_new_version(self):
        deposition_id = self.deposition['id']
        url = '{}/{}/actions/newversion'.format(self.baseurl, deposition_id)
        r = requests.post(url, params=self.params)
        if r.status_code != 201:
            pu.fail("Status {}: {}".format(r.status_code, r.json()))
        url = self.baseurl
        r = requests.get(url, params=self.params)
        if len(r.json()) == 0:
            pu.fail("Status {}: {}".format(r.status_code, r.json()))
        self.deposition = r.json()[0]
        self.record_id = self.deposition['id']

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

            # make sure the URL of the repo is in the metadata
            if 'related_identifiers' not in data:
                data['related_identifiers'] = []

            found = False
            for identifier in data['related_identifiers']:
                if identifier['identifier'] == self.remote_url:
                    found = True
                    break
            if not found:
                data['related_identifiers'].append({
                    "identifier": self.remote_url,
                    "relation": "isSupplementTo",
                    "scheme": "url"
                })

            data['upload_type'] = config['upload_type']
            if config['upload_type'] == 'publication':
                data['publication_type'] = config['publication_type']

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
            pu.fail("{} - Failed to update metadata: {}".format(r.status_code,
                                                                r.json()))

    def delete_previous_file(self):
        url = '{}/{}/files'.format(self.baseurl, self.record_id)
        r = requests.get(url, params=self.params)
        if r.status_code != 200:
            pu.fail("Status {}: {}".format(r.status_code, r.json()))

        if len(r.json()) == 0:
            # no files exist, so we have nothing to do
            return

        old_id = r.json()[0]['id']
        url = '{}/{}/files/{}'.format(self.baseurl, self.record_id, old_id)
        r = requests.delete(url, params=self.params)
        if r.status_code != 204:
            pu.fail("Status {}: {}".format(r.status_code, r.json()))

    def upload_snapshot(self):
        self.update_metadata()
        deposition_id = self.deposition['id']
        new_file = self.create_archive()
        project_root = pu.get_project_root()
        url = '{}/{}/files'.format(self.baseurl, deposition_id)
        data = {'filename': new_file}
        files = {'file': open(os.path.join(project_root, new_file), 'rb')}
        self.delete_archive()
        r = requests.post(url, data=data, files=files, params=self.params)
        if r.status_code != 201:
            pu.fail("Status {}: {}".format(r.status_code, r.json()))

    def publish_snapshot(self):
        url = '{}/{}/actions/publish'.format(self.baseurl, self.record_id)
        r = requests.post(url, params=self.params)
        if r.status_code != 202:
            pu.fail("Status {}: {}".format(r.status_code, r.json()))
        self.is_last_published = True


class Figshare(BaseService):

    def __init__(self, access_token):
        super(Figshare, self).__init__()
        self.baseurl = 'https://api.figshare.com/v2/account/articles'
        self.params = {'access_token': access_token}
        self.doi_prefix = '10.6084/m9.figshare.'
        self.doi_url_prefix = 'https://doi.org/10.6084/m9.figshare.'

    def fetch_depositions(self):
        r = requests.get(self.baseurl, params=self.params)
        if r.status_code == 403:
            pu.fail(
                "The access token provided was invalid. "
                "Please provide a valid access_token."
            )
        elif r.status_code != 200:
            pu.fail("Status {}: {}".format(r.status_code, r.json()))

        depositions = r.json()
        for deposition in depositions:
            deposition_id = deposition['id']
            url = '{}/{}'.format(self.baseurl, deposition_id)
            r = requests.get(url, params=self.params)
            d = r.json()

            if self.remote_url in d['references']:
                self.deposition = d
                self.is_last_published = d['published_date'] is not None
                self.record_id = d['id']
                break

    def create_new_deposition(self):
        url = self.baseurl
        data = {'title': pu.read_config()['metadata']['title']}
        r = requests.post(url, params=self.params, data=json.dumps(data))
        if r.status_code != 201:
            pu.fail("Status {}: {}".format(r.status_code, r.json()))

        location = r.json()['location']
        r = requests.get(location, params=self.params)
        if r.status_code != 200:
            pu.fail("Status {}: {}".format(r.status_code, r.json()))

        self.deposition = r.json()
        self.record_id = self.deposition['id']

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

        if 'references' not in data:
            data['references'] = []
        found = False
        for ref in data['references']:
            if ref == [self.remote_url]:
                found = True
                break
        if not found:
            data['references'].append(self.remote_url)

        url = '{}/{}'.format(self.baseurl, deposition_id)
        r = requests.put(
            url, data=json.dumps(data), params=self.params
        )
        if r.status_code != 205:
            pu.fail("Status {}: {}".format(r.status_code, r.json()))

    def delete_previous_file(self):
        url = '{}/{}/files'.format(self.baseurl, self.record_id)
        r = requests.get(url, params=self.params)
        if r.status_code != 200:
            pu.fail("Status {}: {}".format(r.status_code, r.json()))

        if len(r.json()) == 0:
            return

        old_id = r.json()[0]['id']
        url = '{}/{}/files/{}'.format(self.baseurl, self.record_id, old_id)
        r = requests.delete(url, params=self.params)
        if r.status_code != 204:
            pu.fail("Status {}: {}".format(r.status_code, r.json()))

    def upload_snapshot(self):
        self.update_metadata()
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
        url = '{}/{}/files'.format(self.baseurl, self.record_id)
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
            self.baseurl, self.record_id, file_info['id']
        )
        r = requests.post(url, params=self.params)
        if r.status_code != 202:
            pu.fail("Status {}: {}".format(r.status_code, r.json()))

    def publish_snapshot(self):
        url = '{}/{}/publish'.format(
            self.baseurl, self.deposition['id']
        )
        r = requests.post(url, params=self.params)
        if r.status_code != 201:
            pu.fail("Status {}: {}".format(r.status_code, r.json()))
        self.is_last_published = True
