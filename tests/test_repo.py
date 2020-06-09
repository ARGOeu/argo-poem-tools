#!/usr/bin/python
import os
import sys
import unittest

import mock
import requests
from argo_poem_tools.repos import YUMRepos

mock_data = [
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


def mock_request_ok(*args, **kwargs):
    return MockResponse(mock_data, 200)


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


class YUMReposTests(unittest.TestCase):
    def setUp(self):
        self.repos1 = YUMRepos(
            hostname='mock.url.com',
            token='some-token-1234',
            profiles=['TEST_PROFILE1', 'TEST_PROFILE2']
        )
        self.repos2 = YUMRepos(
            hostname='http://mock.url.com/',
            token='some-token-1234',
            profiles=['TEST_PROFILE1']
        )
        self.repos3 = YUMRepos(
            hostname='https://mock.url.com/',
            token='some-token-1234',
            profiles=['TEST_PROFILE1', 'TEST_PROFILE2']
        )
        self.repos4 = YUMRepos(
            hostname='mock.url.com',
            token='some-token-1234',
            profiles=''
        )

    def tearDown(self):
        if os.path.exists('argo-devel.repo'):
            os.remove('argo-devel.repo')

        if os.path.exists('nordugrid-updates.repo'):
            os.remove('nordugrid-updates.repo')

    if sys.version_info[1] >= 7:
        @mock.patch('argo_poem_tools.repos.subprocess.check_output')
        @mock.patch('argo_poem_tools.repos.requests.get')
        def test_get_data(self, mock_request, mock_sp):
            mock_request.side_effect = mock_request_ok
            mock_sp.return_value = 'centos-release-7-7.1908.0.el7.centos.x86_64'
            data = self.repos1.get_data()
            mock_request.assert_called_once_with(
                'https://mock.url.com/api/v2/repos/centos7',
                headers={'x-api-key': 'some-token-1234',
                         'profiles': '[TEST_PROFILE1, TEST_PROFILE2]'},
                timeout=180
            )
            self.assertEqual(data, mock_data)

        @mock.patch('argo_poem_tools.repos.subprocess.check_output')
        @mock.patch('argo_poem_tools.repos.requests.get')
        def test_get_data_if_hostname_http(self, mock_request, mock_sp):
            mock_request.side_effect = mock_request_ok
            mock_sp.return_value = 'centos-release-7-7.1908.0.el7.centos.x86_64'
            data = self.repos2.get_data()
            mock_request.assert_called_once_with(
                'https://mock.url.com/api/v2/repos/centos7',
                headers={'x-api-key': 'some-token-1234',
                         'profiles': '[TEST_PROFILE1]'},
                timeout=180
            )
            self.assertEqual(data, mock_data)

        @mock.patch('argo_poem_tools.repos.subprocess.check_output')
        @mock.patch('argo_poem_tools.repos.requests.get')
        def test_get_data_if_hostname_https(self, mock_request, mock_sp):
            mock_request.side_effect = mock_request_ok
            mock_sp.return_value = 'centos-release-7-7.1908.0.el7.centos.x86_64'
            data = self.repos1.get_data()
            mock_request.assert_called_once_with(
                'https://mock.url.com/api/v2/repos/centos7',
                headers={'x-api-key': 'some-token-1234',
                         'profiles': '[TEST_PROFILE1, TEST_PROFILE2]'},
                timeout=180
            )
            self.assertEqual(data, mock_data)

        @mock.patch('argo_poem_tools.repos.subprocess.check_output')
        @mock.patch('argo_poem_tools.repos.requests.get')
        def test_get_data_if_server_error(self, mock_request, mock_sp):
            mock_request.side_effect = mock_request_server_error
            mock_sp.return_value = 'centos-release-7-7.1908.0.el7.centos.x86_64'
            with self.assertRaises(requests.exceptions.RequestException) as err:
                self.repos1.get_data()
                self.assertEqual(err, '500 Server Error')

        @mock.patch('argo_poem_tools.repos.subprocess.check_output')
        @mock.patch('argo_poem_tools.repos.requests.get')
        def test_get_data_if_wrong_url(self, mock_request, mock_sp):
            mock_request.side_effect = mock_request_wrong_url
            mock_sp.return_value = 'centos-release-7-7.1908.0.el7.centos.x86_64'
            with self.assertRaises(requests.exceptions.RequestException) as err:
                self.repos1.get_data()
                self.assertEqual(err, '404 Not Found')

        @mock.patch('argo_poem_tools.repos.subprocess.check_output')
        @mock.patch('argo_poem_tools.repos.requests.get')
        def test_get_data_if_wrong_token(self, mock_request, mock_sp):
            mock_request.side_effect = mock_request_wrong_token
            mock_sp.return_value = 'centos-release-7-7.1908.0.el7.centos.x86_64'
            with self.assertRaises(requests.exceptions.RequestException) as err:
                self.repos1.get_data()
                self.assertEqual(
                    err, '403 Forbidden: Authentication credentials were not '
                         'provided.'
                )

        @mock.patch('argo_poem_tools.repos.subprocess.check_output')
        @mock.patch('argo_poem_tools.repos.requests.get')
        def test_get_data_if_no_profiles(self, mock_request, mock_sp):
            mock_request.side_effect = mock_request_wrong_profiles
            mock_sp.return_value = 'centos-release-7-7.1908.0.el7.centos.x86_64'
            with self.assertRaises(requests.exceptions.RequestException) as err:
                self.repos1.get_data()
                self.assertEqual(
                    err, '400 Bad Request: You must define profile!'
                )

        @mock.patch('argo_poem_tools.repos.subprocess.check_output')
        @mock.patch('argo_poem_tools.repos.requests.get')
        def test_get_data_if_json_without_details(
                self, mock_request, mock_sp
        ):
            mock_request.side_effect = mock_request_json_without_details_key
            mock_sp.return_value = 'centos-release-7-7.1908.0.el7.centos.x86_64'
            with self.assertRaises(requests.exceptions.RequestException) as err:
                self.repos1.get_data()
                self.assertEqual(
                    err, '400 Bad Request'
                )

        @mock.patch('argo_poem_tools.repos.subprocess.check_output')
        @mock.patch('argo_poem_tools.repos.requests.get')
        def test_create_file(self, mock_request, mock_sp):
            mock_request.side_effect = mock_request_ok
            mock_sp.return_value = 'centos-release-7-7.1908.0.el7.centos.x86_64'
            self.repos1.create_file(path=os.getcwd())
            mock_request.assert_called_once_with(
                'https://mock.url.com/api/v2/repos/centos7',
                headers={'x-api-key': 'some-token-1234',
                         'profiles': '[TEST_PROFILE1, TEST_PROFILE2]'},
                timeout=180
            )
            self.assertTrue(os.path.exists('argo-devel.repo'))
            self.assertTrue(os.path.exists('nordugrid-updates.repo'))

            with open('argo-devel.repo', 'r') as f:
                content1 = f.read()

            with open('nordugrid-updates.repo', 'r') as f:
                content2 = f.read()

            self.assertEqual(content1, mock_data[0]['argo-devel']['content'])
            self.assertEqual(
                content2, mock_data[0]['nordugrid-updates']['content']
            )

        @mock.patch('argo_poem_tools.repos.subprocess.check_output')
        @mock.patch('argo_poem_tools.repos.requests.get')
        def test_do_override_file_which_already_exists(
                self, mock_request, mock_sp
        ):
            mock_request.side_effect = mock_request_ok
            mock_sp.return_value = 'centos-release-7-7.1908.0.el7.centos.x86_64'
            with open('argo-devel.repo', 'w') as f:
                f.write('test')

            self.repos1.create_file(os.getcwd())
            mock_request.assert_called_once_with(
                'https://mock.url.com/api/v2/repos/centos7',
                headers={'x-api-key': 'some-token-1234',
                         'profiles': '[TEST_PROFILE1, TEST_PROFILE2]'},
                timeout=180
            )
            self.assertTrue(os.path.exists('argo-devel.repo'))
            self.assertTrue(os.path.exists('nordugrid-updates.repo'))

            with open('argo-devel.repo', 'r') as f:
                content1 = f.read()

            with open('nordugrid-updates.repo', 'r') as f:
                content2 = f.read()

            self.assertEqual(content1, mock_data[0]['argo-devel']['content'])
            self.assertEqual(
                content2, mock_data[0]['nordugrid-updates']['content']
            )

    else:
        @mock.patch('argo_poem_tools.repos.subprocess.Popen')
        @mock.patch('argo_poem_tools.repos.requests.get')
        def test_get_data(self, mock_request, mock_sp):
            process_mock = mock.Mock()
            attrs = {
                'communicate.return_value': (
                    'centos-release-6-10.el6.centos.12.3.x86_64',
                    ''
                )
            }
            process_mock.configure_mock(**attrs)
            mock_sp.return_value = process_mock
            mock_request.side_effect = mock_request_ok
            data = self.repos1.get_data()
            mock_request.assert_called_once_with(
                'https://mock.url.com/api/v2/repos/centos6',
                headers={'x-api-key': 'some-token-1234',
                         'profiles': '[TEST_PROFILE1, TEST_PROFILE2]'},
                timeout=180
            )
            self.assertEqual(data, mock_data)

        @mock.patch('argo_poem_tools.repos.subprocess.Popen')
        @mock.patch('argo_poem_tools.repos.requests.get')
        def test_get_data_if_hostname_http(self, mock_request, mock_sp):
            process_mock = mock.Mock()
            attrs = {
                'communicate.return_value': (
                    'centos-release-6-10.el6.centos.12.3.x86_64',
                    ''
                )
            }
            process_mock.configure_mock(**attrs)
            mock_sp.return_value = process_mock
            mock_request.side_effect = mock_request_ok
            data = self.repos2.get_data()
            mock_request.assert_called_once_with(
                'https://mock.url.com/api/v2/repos/centos6',
                headers={'x-api-key': 'some-token-1234',
                         'profiles': '[TEST_PROFILE1]'},
                timeout=180
            )
            self.assertEqual(data, mock_data)

        @mock.patch('argo_poem_tools.repos.subprocess.Popen')
        @mock.patch('argo_poem_tools.repos.requests.get')
        def test_get_data_if_hostname_https(self, mock_request, mock_sp):
            process_mock = mock.Mock()
            attrs = {
                'communicate.return_value': (
                    'centos-release-6-10.el6.centos.12.3.x86_64',
                    ''
                )
            }
            process_mock.configure_mock(**attrs)
            mock_sp.return_value = process_mock
            mock_request.side_effect = mock_request_ok
            data = self.repos1.get_data()
            mock_request.assert_called_once_with(
                'https://mock.url.com/api/v2/repos/centos6',
                headers={'x-api-key': 'some-token-1234',
                         'profiles': '[TEST_PROFILE1, TEST_PROFILE2]'},
                timeout=180
            )
            self.assertEqual(data, mock_data)

        @mock.patch('argo_poem_tools.repos.subprocess.Popen')
        @mock.patch('argo_poem_tools.repos.requests.get')
        def test_get_data_if_server_error(self, mock_request, mock_sp):
            process_mock = mock.Mock()
            attrs = {
                'communicate.return_value': (
                    'centos-release-6-10.el6.centos.12.3.x86_64',
                    ''
                )
            }
            process_mock.configure_mock(**attrs)
            mock_sp.return_value = process_mock
            mock_request.side_effect = mock_request_server_error
            self.assertRaises(
                requests.exceptions.RequestException,
                self.repos1.get_data
            )

        @mock.patch('argo_poem_tools.repos.subprocess.Popen')
        @mock.patch('argo_poem_tools.repos.requests.get')
        def test_get_data_if_wrong_url(self, mock_request, mock_sp):
            process_mock = mock.Mock()
            attrs = {
                'communicate.return_value': (
                    'centos-release-6-10.el6.centos.12.3.x86_64',
                    ''
                )
            }
            process_mock.configure_mock(**attrs)
            mock_sp.return_value = process_mock
            mock_request.side_effect = mock_request_wrong_url
            self.assertRaises(
                requests.exceptions.RequestException,
                self.repos1.get_data
            )

        @mock.patch('argo_poem_tools.repos.subprocess.Popen')
        @mock.patch('argo_poem_tools.repos.requests.get')
        def test_get_data_if_wrong_token(self, mock_request, mock_sp):
            process_mock = mock.Mock()
            attrs = {
                'communicate.return_value': (
                    'centos-release-6-10.el6.centos.12.3.x86_64',
                    ''
                )
            }
            process_mock.configure_mock(**attrs)
            mock_sp.return_value = process_mock
            mock_request.side_effect = mock_request_wrong_token
            self.assertRaises(
                requests.exceptions.RequestException,
                self.repos1.get_data
            )

        @mock.patch('argo_poem_tools.repos.subprocess.Popen')
        @mock.patch('argo_poem_tools.repos.requests.get')
        def test_get_data_if_no_profiles(self, mock_request, mock_sp):
            process_mock = mock.Mock()
            attrs = {
                'communicate.return_value': (
                    'centos-release-6-10.el6.centos.12.3.x86_64',
                    ''
                )
            }
            process_mock.configure_mock(**attrs)
            mock_sp.return_value = process_mock
            mock_request.side_effect = mock_request_wrong_profiles
            self.assertRaises(
                requests.exceptions.RequestException,
                self.repos1.get_data
            )

        @mock.patch('argo_poem_tools.repos.subprocess.Popen')
        @mock.patch('argo_poem_tools.repos.requests.get')
        def test_get_data_if_json_without_details(
                self, mock_request, mock_sp
        ):
            process_mock = mock.Mock()
            attrs = {
                'communicate.return_value': (
                    'centos-release-6-10.el6.centos.12.3.x86_64',
                    ''
                )
            }
            process_mock.configure_mock(**attrs)
            mock_sp.return_value = process_mock
            mock_request.side_effect = mock_request_json_without_details_key
            self.assertRaises(
                requests.exceptions.RequestException,
                self.repos1.get_data
            )

        @mock.patch('argo_poem_tools.repos.subprocess.Popen')
        @mock.patch('argo_poem_tools.repos.requests.get')
        def test_create_file(self, mock_request, mock_sp):
            process_mock = mock.Mock()
            attrs = {
                'communicate.return_value': (
                    'centos-release-6-10.el6.centos.12.3.x86_64',
                    ''
                )
            }
            process_mock.configure_mock(**attrs)
            mock_sp.return_value = process_mock
            mock_request.side_effect = mock_request_ok
            self.repos1.create_file(path=os.getcwd())
            mock_request.assert_called_once_with(
                'https://mock.url.com/api/v2/repos/centos6',
                headers={'x-api-key': 'some-token-1234',
                         'profiles': '[TEST_PROFILE1, TEST_PROFILE2]'},
                timeout=180
            )
            self.assertTrue(os.path.exists('argo-devel.repo'))
            self.assertTrue(os.path.exists('nordugrid-updates.repo'))

            with open('argo-devel.repo', 'r') as f:
                content1 = f.read()

            with open('nordugrid-updates.repo', 'r') as f:
                content2 = f.read()

            self.assertEqual(content1, mock_data[0]['argo-devel']['content'])
            self.assertEqual(
                content2, mock_data[0]['nordugrid-updates']['content']
            )

        @mock.patch('argo_poem_tools.repos.subprocess.Popen')
        @mock.patch('argo_poem_tools.repos.requests.get')
        def test_do_override_file_which_already_exists(
                self, mock_request, mock_sp
        ):
            process_mock = mock.Mock()
            attrs = {
                'communicate.return_value': (
                    'centos-release-6-10.el6.centos.12.3.x86_64',
                    ''
                )
            }
            process_mock.configure_mock(**attrs)
            mock_sp.return_value = process_mock
            mock_request.side_effect = mock_request_ok
            with open('argo-devel.repo', 'w') as f:
                f.write('test')

            self.repos1.create_file(os.getcwd())
            mock_request.assert_called_once_with(
                'https://mock.url.com/api/v2/repos/centos6',
                headers={'x-api-key': 'some-token-1234',
                         'profiles': '[TEST_PROFILE1, TEST_PROFILE2]'},
                timeout=180
            )
            self.assertTrue(os.path.exists('argo-devel.repo'))
            self.assertTrue(os.path.exists('nordugrid-updates.repo'))

            with open('argo-devel.repo', 'r') as f:
                content1 = f.read()

            with open('nordugrid-updates.repo', 'r') as f:
                content2 = f.read()

            self.assertEqual(content1, mock_data[0]['argo-devel']['content'])
            self.assertEqual(
                content2, mock_data[0]['nordugrid-updates']['content']
            )


if __name__ == '__main__':
    unittest.main()
