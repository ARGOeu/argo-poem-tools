import os
import shutil
import subprocess

import requests


class YUMRepos:
    def __init__(self, hostname, token, profiles, override=True):
        self.hostname = hostname
        self.token = token
        self.profiles = profiles
        self.data = None
        self.missing_packages = None
        self.override = override

    def get_data(self):
        headers = {
            'x-api-key': self.token,
            'profiles': self._refine_list_of_profiles()
        }
        response = requests.get(self._build_url(), headers=headers, timeout=180)

        if response.status_code == 200:
            data = response.json()
            self.data = data['data']
            self.missing_packages = data['missing_packages']
            return self.data

        else:
            try:
                msg = response.json()['detail']

            except (ValueError, TypeError, KeyError):
                msg = '%s %s' % (response.status_code, response.reason)

            raise requests.exceptions.RequestException(msg)

    def create_file(self, path='/etc/yum.repos.d'):
        if not self.data:
            self.get_data()

        files = []
        for key, value in self.data.items():
            title = key
            filename = os.path.join(path, title + '.repo')
            content = value['content']

            files.append(filename)

            if not self.override:
                shutil.copytree(filename, os.path.join('/tmp', filename))

            with open(filename, 'w') as f:
                f.write(content)

        return sorted(files)

    @classmethod
    def _get_centos_version(cls):
        string = subprocess.check_output(['rpm', '-q', 'centos-release'])

        string = string.decode('utf-8')

        return 'centos' + string.split('-')[2]

    def _build_url(self):
        hostname = self.hostname
        if hostname.startswith('https://'):
            hostname = hostname[8:]

        if hostname.startswith('http://'):
            hostname = hostname[7:]

        if hostname.endswith('/'):
            hostname = hostname[0:-1]

        return 'https://' + hostname + '/api/v2/repos/' + \
               self._get_centos_version()

    def _refine_list_of_profiles(self):
        return '[' + ', '.join(self.profiles) + ']'
