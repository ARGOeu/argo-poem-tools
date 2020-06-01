#!/usr/bin/python
import os
import requests
import subprocess
import sys


def get_repo_data(url, token, profiles):
    headers = {
        'x-api-key': token, 'profiles': refine_list_of_profiles(profiles)
    }
    response = requests.get(url, headers=headers, timeout=180)

    if response.status_code == 200:
        if response.json():
            return response.json()

    else:
        try:
            msg = response.json()['detail']

        except (ValueError, TypeError):
            msg = '%s %s' % (response.status_code, response.reason)

        raise requests.exceptions.RequestException(msg)


def create_yum_repo_file(data, path='/etc/yum.repos.d'):
    for key, value in data[0].items():
        title = key
        content = value['content']

        with open(os.path.join(path, title + '.repo'), 'w') as f:
            f.write(content)


def get_centos_version():
    if sys.version_info[1] >= 7:
        string = subprocess.check_output(['rpm', '-q', 'centos-release'])

    else:
        string = subprocess.Popen(
            ['rpm', '-q', 'centos-release'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        ).communicate()[0]

    return 'centos' + string.split('-')[2]


def build_api_url(hostname):
    if hostname.startswith('https://'):
        hostname = hostname[8:]

    if hostname.startswith('http://'):
        hostname = hostname[7:]

    if hostname.endswith('/'):
        hostname = hostname[0:-1]

    return 'https://' + hostname + '/api/v2/repos/' + get_centos_version()


def refine_list_of_profiles(profiles):
    profiles = '[' + ', '.join(profiles) + ']'

    return profiles
