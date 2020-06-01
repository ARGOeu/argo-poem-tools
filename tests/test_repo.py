#!/usr/bin/python
import mock

from argo_poem_tools.repos import create_yum_repo_file, get_centos_version, \
    build_api_url, refine_list_of_profiles, get_repo_data

import os
import requests
import sys
import unittest


data = [
    {
        "argo-devel": {
            "content": "[argo-devel]\n"
                       "name=ARGO Product Repository\n"
                       "baseurl=http://rpm-repo.argo.grnet.gr/ARGO/"
                       "devel/centos6/\n"
                       "gpgcheck=0\n"
                       "enabled=1\n"
                       "priority=99\n"
                       "exclude=\n"
                       "includepkgs=\n",
            "packages": [
                {
                    "name": "nagios-plugins-fedcloud",
                    "version": "0.5.0"
                },
                {
                    "name": "nagios-plugins-igtf",
                    "version": "1.4.0"
                },
                {
                    "name": "nagios-plugins-globus",
                    "version": "0.1.5"
                }
            ]
        },
        "nordugrid-updates": {
            "content": "[nordugrid-updates]\n"
                       "name=NorduGrid - $basearch - Updates\n"
                       "baseurl=http://download.nordugrid.org/repos/6"
                       "/centos/el6/$basearch/updates\n"
                       "enabled=1\n"
                       "gpgcheck=1\n"
                       "gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-"
                       "nordugrid-6\n"
                       "priority=1\n"
                       "exclude=ca_*\n",
            "packages": [
                {
                    "name": "nordugrid-arc-nagios-plugins",
                    "version": "2.0.0"
                }
            ]
        }
    }
]


class MockResponse:
    def __init__(self, dat, status_code):
        self.data = dat
        self.status_code = status_code
        if status_code == 404:
            self.reason = 'Not Found'

        elif status_code == 403:
            self.reason = 'Forbidden'

        elif status_code == 400:
            self.reason = 'Bad Request'

        elif status_code == 500:
            self.reason = 'Server Error'

    def json(self):
        return self.data


def mock_request(*args, **kwargs):
    return MockResponse(data, 200)


def mock_request_wrong_url(*args, **kwargs):
    return MockResponse(
        '<h1>Not Found</h1>\n'
        '<p>The requested resource was not found on this server.</p>', 404
    )


def mock_request_wrong_token(*args, **kwargs):
    return MockResponse(
        {"detail": "Authentication credentials were not provided."}, 403
    )


def mock_request_wrong_profiles(*args, **kwargs):
    return MockResponse(
        {"detail": "You must define profile!"}, 400
    )


def mock_request_server_error(*args, **kwargs):
    return MockResponse('<h1>Server Error (500)</h1>', 500)


def mock_request_json_without_details_key(*args, **kwargs):
    return MockResponse(
        {'error': 'Your error message is not correct'}, 400
    )


class RepoTests(unittest.TestCase):
    def tearDown(self):
        if os.path.exists('argo-devel.repo'):
            os.remove('argo-devel.repo')

        if os.path.exists('nordugrid-updates.repo'):
            os.remove('nordugrid-updates.repo')

    def test_create_yum_repo_file(self):
        create_yum_repo_file(data, os.getcwd())
        self.assertTrue(os.path.exists('argo-devel.repo'))
        self.assertTrue(os.path.exists('nordugrid-updates.repo'))

        with open('argo-devel.repo', 'r') as f:
            content1 = f.read()

        with open('nordugrid-updates.repo', 'r') as f:
            content2 = f.read()

        self.assertEqual(content1, data[0]['argo-devel']['content'])
        self.assertEqual(content2, data[0]['nordugrid-updates']['content'])

    def test_do_override_file_which_already_exists(self):
        with open('argo-devel.repo', 'w') as f:
            f.write('test')

        create_yum_repo_file(data, os.getcwd())
        self.assertTrue(os.path.exists('argo-devel.repo'))
        self.assertTrue(os.path.exists('nordugrid-updates.repo'))

        with open('argo-devel.repo', 'r') as f:
            content1 = f.read()

        with open('nordugrid-updates.repo', 'r') as f:
            content2 = f.read()

        self.assertEqual(content1, data[0]['argo-devel']['content'])
        self.assertEqual(content2, data[0]['nordugrid-updates']['content'])

    if sys.version_info[1] >= 7:
        @mock.patch('subprocess.check_output')
        def test_centos_version_7(self, func):
            func.return_value = 'centos-release-7-7.1908.0.el7.centos.x86_64'
            self.assertEqual(get_centos_version(), 'centos7')

    else:
        @mock.patch('subprocess.Popen')
        def test_centos_version_6(self, func):
            process_mock = mock.Mock()
            attrs = {
                'communicate.return_value': (
                    'centos-release-6-10.el6.centos.12.3.x86_64',
                    ''
                )
            }
            process_mock.configure_mock(**attrs)
            func.return_value = process_mock
            self.assertEqual(get_centos_version(), 'centos6')

    @mock.patch('argo_poem_tools.repos.get_centos_version')
    def test_build_api_url(self, func):
        func.return_value = 'centos7'
        self.assertEqual(
            build_api_url('egi.tenant.com'),
            'https://egi.tenant.com/api/v2/repos/centos7'
        )

    @mock.patch('argo_poem_tools.repos.get_centos_version')
    def test_build_api_url_if_hostname_with_http(self, func):
        func.return_value = 'centos7'
        self.assertEqual(
            build_api_url('http://egi.tenant.com'),
            'https://egi.tenant.com/api/v2/repos/centos7'
        )

    @mock.patch('argo_poem_tools.repos.get_centos_version')
    def test_build_api_url_if_hostname_with_https(self, func):
        func.return_value = 'centos7'
        self.assertEqual(
            build_api_url('https://egi.tenant.com'),
            'https://egi.tenant.com/api/v2/repos/centos7'
        )

    @mock.patch('argo_poem_tools.repos.get_centos_version')
    def test_build_api_url_if_hostname_with_trailing_slash(self, func):
        func.return_value = 'centos7'
        self.assertEqual(
            build_api_url('egi.tenant.com/'),
            'https://egi.tenant.com/api/v2/repos/centos7'
        )

    @mock.patch('argo_poem_tools.repos.get_centos_version')
    def test_build_api_url_if_hostname_with_trailing_slash_and_http(self, func):
        func.return_value = 'centos7'
        self.assertEqual(
            build_api_url('http://egi.tenant.com/'),
            'https://egi.tenant.com/api/v2/repos/centos7'
        )

    def test_refine_profiles(self):
        self.assertEqual(
            refine_list_of_profiles(['ARGO_MON', 'ARGO_MON_TEST']),
            '[ARGO_MON, ARGO_MON_TEST]'
        )

    def test_refine_profiles_if_one(self):
        self.assertEqual(
            refine_list_of_profiles(['ARGO_MON']),
            '[ARGO_MON]'
        )

    @mock.patch('requests.get', side_effect=mock_request)
    def test_get_repo_data(self, func):
        self.assertEqual(
            get_repo_data('url', 'token', 'profiles'),
            data
        )

    @mock.patch('requests.get', side_effect=mock_request_wrong_url)
    def test_get_repo_data_if_wrong_url(self, func):
        self.assertRaises(
            requests.exceptions.RequestException,
            get_repo_data,
            url='wrong-url',
            token='token',
            profiles='profiles'
        )

    @mock.patch('requests.get', side_effect=mock_request_wrong_token)
    def test_get_repo_data_if_wrong_token(self, func):
        self.assertRaises(
            requests.exceptions.RequestException,
            get_repo_data,
            url='url',
            token='wrong-token',
            profiles='profiles'
        )

    @mock.patch('requests.get', side_effect=mock_request_wrong_profiles)
    def test_get_repo_data_if_wrong_profiles(self, func):
        self.assertRaises(
            requests.exceptions.RequestException,
            get_repo_data,
            url='url',
            token='token',
            profiles=''
        )

    @mock.patch('requests.get', side_effect=mock_request_server_error)
    def test_get_repo_data_if_server_error(self, func):
        self.assertRaises(
            requests.exceptions.RequestException,
            get_repo_data,
            url='url',
            token='token',
            profiles='profiles'
        )

    @mock.patch('requests.get')
    def test_get_repo_data_if_json_without_details(self, mock_request):
        mock_request.side_effect = mock_request_json_without_details_key
        self.assertRaises(
            requests.exceptions.RequestException,
            get_repo_data,
            url='url',
            token='token',
            profiles='profiles'
        )


if __name__ == '__main__':
    unittest.main()
