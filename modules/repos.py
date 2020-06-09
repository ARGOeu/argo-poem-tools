import os
import subprocess
import sys

import requests


class YUMRepos:
    def __init__(self, hostname, token, profiles):
        self.hostname = hostname
        self.token = token
        self.profiles = profiles

    def get_data(self):
        headers = {
            'x-api-key': self.token,
            'profiles': self._refine_list_of_profiles()
        }
        response = requests.get(self._build_url(), headers=headers, timeout=180)

        if response.status_code == 200:
            data = response.json()
            return data

        else:
            try:
                msg = response.json()['detail']

            except (ValueError, TypeError, KeyError):
                msg = '%s %s' % (response.status_code, response.reason)

            raise requests.exceptions.RequestException(msg)

    def create_file(self, path='/etc/yum.repos.d'):
        data = self.get_data()

        for key, value in data[0].items():
            title = key
            content = value['content']

            with open(os.path.join(path, title + '.repo'), 'w') as f:
                f.write(content)

    @classmethod
    def _get_centos_version(cls):
        if sys.version_info[1] >= 7:
            string = subprocess.check_output(['rpm', '-q', 'centos-release'])

        else:
            string = subprocess.Popen(
                ['rpm', '-q', 'centos-release'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            ).communicate()[0]

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
