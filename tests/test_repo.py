import os
import unittest
from unittest import mock

import requests
from argo_poem_tools.repos import YUMRepos

mock_data = {
    "data": {
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
                    "name": "nagios-plugins-globus",
                    "version": "0.1.5"
                },
                {
                    "name": "nagios-plugins-igtf",
                    "version": "1.4.0"
                },
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
    },
    "missing_packages": [
        "nagios-plugins-bdii (1.0.14)",
        "nagios-plugins-egi-notebooks (0.2.3)"]
}

mock_data_internal_metrics = {
    "data": {
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
                    "name": "argo-probe-ams-publisher",
                    "version": "present"
                },
                {
                    "name": "argo-probe-argo-tools",
                    "version": "0.1.1"
                },
                {
                    "name": "argo-probe-oidc",
                    "version": "present"
                },
                {
                    "name": "nagios-plugins-igtf",
                    "version": "1.4.0"
                }
            ]
        }
    },
    "missing_packages": []
}


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
    if "repos_internal" in args[0]:
        return MockResponse(mock_data_internal_metrics, 200)

    else:
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
            profiles=['TEST_PROFILE1', 'TEST_PROFILE2'],
            repos_path=os.getcwd()
        )
        self.repos2 = YUMRepos(
            hostname='http://mock.url.com/',
            token='some-token-1234',
            profiles=['TEST_PROFILE1'],
            repos_path=os.getcwd()
        )
        self.repos3 = YUMRepos(
            hostname='https://mock.url.com/',
            token='some-token-1234',
            profiles=['TEST_PROFILE1', 'TEST_PROFILE2'],
            repos_path=os.getcwd()
        )
        self.repos4 = YUMRepos(
            hostname='mock.url.com',
            token='some-token-1234',
            profiles='',
            repos_path=os.getcwd()
        )
        self.repos5 = YUMRepos(
            hostname='mock.url.com',
            token='some-token-1234',
            profiles=['TEST_PROFILE1', 'TEST_PROFILE2'],
            repos_path=os.getcwd(),
            override=False
        )

    def tearDown(self):
        if os.path.exists('argo-devel.repo'):
            os.remove('argo-devel.repo')

        if os.path.exists('nordugrid-updates.repo'):
            os.remove('nordugrid-updates.repo')

    @mock.patch('argo_poem_tools.repos.subprocess.check_output')
    @mock.patch('argo_poem_tools.repos.requests.get')
    def test_get_data(self, mock_request, mock_sp):
        mock_request.side_effect = mock_request_ok
        mock_sp.return_value = \
            'centos-release-7-7.1908.0.el7.centos.x86_64'.encode('utf-8')
        data = self.repos1.get_data()
        mock_request.assert_called_once_with(
            'https://mock.url.com/api/v2/repos/centos7',
            headers={'x-api-key': 'some-token-1234',
                     'profiles': '[TEST_PROFILE1, TEST_PROFILE2]'},
            timeout=180
        )
        self.assertEqual(data, mock_data['data'])
        self.assertEqual(
            self.repos1.missing_packages,
            [
                'nagios-plugins-bdii (1.0.14)',
                'nagios-plugins-egi-notebooks (0.2.3)'
            ]
        )

    @mock.patch('argo_poem_tools.repos.subprocess.check_output')
    @mock.patch('argo_poem_tools.repos.requests.get')
    def test_get_data_including_internal_metrics(self, mock_request, mock_sp):
        mock_request.side_effect = mock_request_ok
        mock_sp.return_value = \
            'centos-release-7-7.1908.0.el7.centos.x86_64'.encode('utf-8')
        data = self.repos1.get_data(include_internal=True)
        self.assertEqual(mock_request.call_count, 2)
        mock_request.assert_has_calls([
            mock.call(
                "https://mock.url.com/api/v2/repos/centos7",
                headers={'x-api-key': 'some-token-1234',
                         'profiles': '[TEST_PROFILE1, TEST_PROFILE2]'},
                timeout=180
            ),
            mock.call(
                "https://mock.url.com/api/v2/repos_internal/centos7",
                headers={'x-api-key': 'some-token-1234'},
                timeout=180
            )
        ], any_order=True)
        self.assertEqual(
            data, {
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
                            "name": "argo-probe-ams-publisher",
                            "version": "present"
                        },
                        {
                            "name": "argo-probe-argo-tools",
                            "version": "0.1.1"
                        },
                        {
                            "name": "argo-probe-oidc",
                            "version": "present"
                        },
                        {
                            "name": "nagios-plugins-fedcloud",
                            "version": "0.5.0"
                        },
                        {
                            "name": "nagios-plugins-globus",
                            "version": "0.1.5"
                        },
                        {
                            "name": "nagios-plugins-igtf",
                            "version": "1.4.0"
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
        )
        self.assertEqual(
            self.repos1.missing_packages,
            [
                'nagios-plugins-bdii (1.0.14)',
                'nagios-plugins-egi-notebooks (0.2.3)'
            ]
        )

    @mock.patch('argo_poem_tools.repos.subprocess.check_output')
    @mock.patch('argo_poem_tools.repos.requests.get')
    def test_get_data_if_hostname_http(self, mock_request, mock_sp):
        mock_request.side_effect = mock_request_ok
        mock_sp.return_value = \
            'centos-release-7-7.1908.0.el7.centos.x86_64'.encode('utf-8')
        data = self.repos2.get_data()
        mock_request.assert_called_once_with(
            'https://mock.url.com/api/v2/repos/centos7',
            headers={'x-api-key': 'some-token-1234',
                     'profiles': '[TEST_PROFILE1]'},
            timeout=180
        )
        self.assertEqual(data, mock_data['data'])
        self.assertEqual(
            self.repos2.missing_packages,
            [
                'nagios-plugins-bdii (1.0.14)',
                'nagios-plugins-egi-notebooks (0.2.3)'
            ]
        )

    @mock.patch('argo_poem_tools.repos.subprocess.check_output')
    @mock.patch('argo_poem_tools.repos.requests.get')
    def test_get_data_if_hostname_http_including_internal(
            self, mock_request, mock_sp
    ):
        mock_request.side_effect = mock_request_ok
        mock_sp.return_value = \
            'centos-release-7-7.1908.0.el7.centos.x86_64'.encode('utf-8')
        data = self.repos2.get_data(include_internal=True)
        mock_request.assert_has_calls([
            mock.call(
                "https://mock.url.com/api/v2/repos/centos7",
                headers={'x-api-key': 'some-token-1234',
                         'profiles': '[TEST_PROFILE1]'},
                timeout=180
            ),
            mock.call(
                "https://mock.url.com/api/v2/repos_internal/centos7",
                headers={'x-api-key': 'some-token-1234'},
                timeout=180
            )
        ], any_order=True)
        self.assertEqual(
            data, {
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
                            "name": "argo-probe-ams-publisher",
                            "version": "present"
                        },
                        {
                            "name": "argo-probe-argo-tools",
                            "version": "0.1.1"
                        },
                        {
                            "name": "argo-probe-oidc",
                            "version": "present"
                        },
                        {
                            "name": "nagios-plugins-fedcloud",
                            "version": "0.5.0"
                        },
                        {
                            "name": "nagios-plugins-globus",
                            "version": "0.1.5"
                        },
                        {
                            "name": "nagios-plugins-igtf",
                            "version": "1.4.0"
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
        )
        self.assertEqual(
            self.repos2.missing_packages,
            [
                'nagios-plugins-bdii (1.0.14)',
                'nagios-plugins-egi-notebooks (0.2.3)'
            ]
        )

    @mock.patch('argo_poem_tools.repos.subprocess.check_output')
    @mock.patch('argo_poem_tools.repos.requests.get')
    def test_get_data_if_hostname_https(self, mock_request, mock_sp):
        mock_request.side_effect = mock_request_ok
        mock_sp.return_value = \
            'centos-release-7-7.1908.0.el7.centos.x86_64'.encode('utf-8')
        data = self.repos3.get_data()
        mock_request.assert_called_once_with(
            'https://mock.url.com/api/v2/repos/centos7',
            headers={'x-api-key': 'some-token-1234',
                     'profiles': '[TEST_PROFILE1, TEST_PROFILE2]'},
            timeout=180
        )
        self.assertEqual(data, mock_data['data'])
        self.assertEqual(
            self.repos3.missing_packages,
            [
                'nagios-plugins-bdii (1.0.14)',
                'nagios-plugins-egi-notebooks (0.2.3)'
            ]
        )

    @mock.patch('argo_poem_tools.repos.subprocess.check_output')
    @mock.patch('argo_poem_tools.repos.requests.get')
    def test_get_data_if_hostname_https_including_internal(
            self, mock_request, mock_sp
    ):
        mock_request.side_effect = mock_request_ok
        mock_sp.return_value = \
            'centos-release-7-7.1908.0.el7.centos.x86_64'.encode('utf-8')
        data = self.repos3.get_data(include_internal=True)
        mock_request.assert_has_calls([
            mock.call(
                "https://mock.url.com/api/v2/repos/centos7",
                headers={'x-api-key': 'some-token-1234',
                         'profiles': '[TEST_PROFILE1, TEST_PROFILE2]'},
                timeout=180
            ),
            mock.call(
                "https://mock.url.com/api/v2/repos_internal/centos7",
                headers={'x-api-key': 'some-token-1234'},
                timeout=180
            )
        ], any_order=True)
        self.assertEqual(
            data, {
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
                            "name": "argo-probe-ams-publisher",
                            "version": "present"
                        },
                        {
                            "name": "argo-probe-argo-tools",
                            "version": "0.1.1"
                        },
                        {
                            "name": "argo-probe-oidc",
                            "version": "present"
                        },
                        {
                            "name": "nagios-plugins-fedcloud",
                            "version": "0.5.0"
                        },
                        {
                            "name": "nagios-plugins-globus",
                            "version": "0.1.5"
                        },
                        {
                            "name": "nagios-plugins-igtf",
                            "version": "1.4.0"
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
        )
        self.assertEqual(
            self.repos3.missing_packages,
            [
                'nagios-plugins-bdii (1.0.14)',
                'nagios-plugins-egi-notebooks (0.2.3)'
            ]
        )

    @mock.patch('argo_poem_tools.repos.subprocess.check_output')
    @mock.patch('argo_poem_tools.repos.requests.get')
    def test_get_data_if_server_error(self, mock_request, mock_sp):
        mock_request.side_effect = mock_request_server_error
        mock_sp.return_value = \
            'centos-release-7-7.1908.0.el7.centos.x86_64'.encode('utf-8')
        with self.assertRaises(requests.exceptions.RequestException) as err:
            self.repos1.get_data()
            self.assertEqual(err, '500 Server Error')

    @mock.patch('argo_poem_tools.repos.subprocess.check_output')
    @mock.patch('argo_poem_tools.repos.requests.get')
    def test_get_data_if_server_error_including_internal(
            self, mock_request, mock_sp
    ):
        mock_request.side_effect = mock_request_server_error
        mock_sp.return_value = \
            'centos-release-7-7.1908.0.el7.centos.x86_64'.encode('utf-8')
        with self.assertRaises(requests.exceptions.RequestException) as err:
            self.repos1.get_data(include_internal=True)
            self.assertEqual(err, '500 Server Error')

    @mock.patch('argo_poem_tools.repos.subprocess.check_output')
    @mock.patch('argo_poem_tools.repos.requests.get')
    def test_get_data_if_wrong_url(self, mock_request, mock_sp):
        mock_request.side_effect = mock_request_wrong_url
        mock_sp.return_value = \
            'centos-release-7-7.1908.0.el7.centos.x86_64'.encode('utf-8')
        with self.assertRaises(requests.exceptions.RequestException) as err:
            self.repos1.get_data()
            self.assertEqual(err, '404 Not Found')

    @mock.patch('argo_poem_tools.repos.subprocess.check_output')
    @mock.patch('argo_poem_tools.repos.requests.get')
    def test_get_data_if_wrong_token(self, mock_request, mock_sp):
        mock_request.side_effect = mock_request_wrong_token
        mock_sp.return_value = \
            'centos-release-7-7.1908.0.el7.centos.x86_64'.encode('utf-8')
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
        mock_sp.return_value = \
            'centos-release-7-7.1908.0.el7.centos.x86_64'.encode('utf-8')
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
        mock_sp.return_value = \
            'centos-release-7-7.1908.0.el7.centos.x86_64'.encode('utf-8')
        with self.assertRaises(requests.exceptions.RequestException) as err:
            self.repos1.get_data()
            self.assertEqual(
                err, '400 Bad Request'
            )

    @mock.patch('argo_poem_tools.repos.subprocess.check_output')
    @mock.patch('argo_poem_tools.repos.YUMRepos.get_data')
    def test_create_file(self, mock_get_data, mock_sp):
        mock_get_data.return_value = mock_data["data"]
        mock_sp.return_value = \
            'centos-release-7-7.1908.0.el7.centos.x86_64'.encode('utf-8')
        files = self.repos1.create_file()
        mock_get_data.assert_called_once_with(include_internal=False)
        self.assertEqual(
            files,
            [os.path.join(os.getcwd(), 'argo-devel.repo'),
             os.path.join(os.getcwd(), 'nordugrid-updates.repo')]
        )
        self.assertTrue(os.path.exists('argo-devel.repo'))
        self.assertTrue(os.path.exists('nordugrid-updates.repo'))

        with open('argo-devel.repo', 'r') as f:
            content1 = f.read()

        with open('nordugrid-updates.repo', 'r') as f:
            content2 = f.read()

        self.assertEqual(
            content1, mock_data['data']['argo-devel']['content']
        )
        self.assertEqual(
            content2, mock_data['data']['nordugrid-updates']['content']
        )

    @mock.patch('argo_poem_tools.repos.subprocess.check_output')
    @mock.patch('argo_poem_tools.repos.YUMRepos.get_data')
    def test_create_file_including_internal(self, mock_get_data, mock_sp):
        mock_get_data.return_value = mock_data["data"]
        mock_sp.return_value = \
            'centos-release-7-7.1908.0.el7.centos.x86_64'.encode('utf-8')
        files = self.repos1.create_file(include_internal=True)
        mock_get_data.assert_called_once_with(include_internal=True)
        self.assertEqual(
            files,
            [os.path.join(os.getcwd(), 'argo-devel.repo'),
             os.path.join(os.getcwd(), 'nordugrid-updates.repo')]
        )
        self.assertTrue(os.path.exists('argo-devel.repo'))
        self.assertTrue(os.path.exists('nordugrid-updates.repo'))

        with open('argo-devel.repo', 'r') as f:
            content1 = f.read()

        with open('nordugrid-updates.repo', 'r') as f:
            content2 = f.read()

        self.assertEqual(
            content1, mock_data['data']['argo-devel']['content']
        )
        self.assertEqual(
            content2, mock_data['data']['nordugrid-updates']['content']
        )

    @mock.patch('argo_poem_tools.repos.shutil.copyfile')
    @mock.patch('argo_poem_tools.repos.os.path.isfile')
    @mock.patch('argo_poem_tools.repos.os.makedirs')
    @mock.patch('argo_poem_tools.repos.subprocess.check_output')
    @mock.patch('argo_poem_tools.repos.YUMRepos.get_data')
    def test_do_override_file_which_already_exists(
            self, mock_get_data, mock_sp, mock_mkdir, mock_isfile, mock_cp
    ):
        mock_get_data.return_value = mock_data["data"]
        mock_sp.return_value = \
            'centos-release-7-7.1908.0.el7.centos.x86_64'.encode('utf-8')
        with open('argo-devel.repo', 'w') as f:
            f.write('test')

        files = self.repos1.create_file()
        mock_get_data.assert_called_once_with(include_internal=False)
        self.assertFalse(mock_mkdir.called)
        self.assertFalse(mock_isfile.called)
        self.assertFalse(mock_cp.called)
        self.assertEqual(
            files,
            [os.path.join(os.getcwd(), 'argo-devel.repo'),
             os.path.join(os.getcwd(), 'nordugrid-updates.repo')]
        )
        self.assertTrue(os.path.exists('argo-devel.repo'))
        self.assertTrue(os.path.exists('nordugrid-updates.repo'))

        with open('argo-devel.repo', 'r') as f:
            content1 = f.read()

        with open('nordugrid-updates.repo', 'r') as f:
            content2 = f.read()

        self.assertEqual(
            content1, mock_data['data']['argo-devel']['content']
        )
        self.assertEqual(
            content2, mock_data['data']['nordugrid-updates']['content']
        )

    @mock.patch('argo_poem_tools.repos.shutil.copyfile')
    @mock.patch('argo_poem_tools.repos.os.path.isfile')
    @mock.patch('argo_poem_tools.repos.os.makedirs')
    @mock.patch('argo_poem_tools.repos.subprocess.check_output')
    @mock.patch('argo_poem_tools.repos.YUMRepos.get_data')
    def test_do_override_file_which_already_exists_including_internal(
            self, mock_get_data, mock_sp, mock_mkdir, mock_isfile, mock_cp
    ):
        mock_get_data.return_value = mock_data["data"]
        mock_sp.return_value = \
            'centos-release-7-7.1908.0.el7.centos.x86_64'.encode('utf-8')
        with open('argo-devel.repo', 'w') as f:
            f.write('test')

        files = self.repos1.create_file(include_internal=True)
        mock_get_data.assert_called_once_with(include_internal=True)
        self.assertFalse(mock_mkdir.called)
        self.assertFalse(mock_isfile.called)
        self.assertFalse(mock_cp.called)
        self.assertEqual(
            files,
            [os.path.join(os.getcwd(), 'argo-devel.repo'),
             os.path.join(os.getcwd(), 'nordugrid-updates.repo')]
        )
        self.assertTrue(os.path.exists('argo-devel.repo'))
        self.assertTrue(os.path.exists('nordugrid-updates.repo'))

        with open('argo-devel.repo', 'r') as f:
            content1 = f.read()

        with open('nordugrid-updates.repo', 'r') as f:
            content2 = f.read()

        self.assertEqual(
            content1, mock_data['data']['argo-devel']['content']
        )
        self.assertEqual(
            content2, mock_data['data']['nordugrid-updates']['content']
        )

    @mock.patch('argo_poem_tools.repos.shutil.copyfile')
    @mock.patch('argo_poem_tools.repos.os.path.isfile')
    @mock.patch('argo_poem_tools.repos.os.makedirs')
    @mock.patch('argo_poem_tools.repos.subprocess.check_output')
    @mock.patch('argo_poem_tools.repos.YUMRepos.get_data')
    def test_do_not_override_file_which_already_exists(
            self, mock_get_data, mock_sp, mock_mkdir, mock_isfile, mock_copy
    ):
        mock_get_data.return_value = mock_data["data"]
        mock_sp.return_value = \
            'centos-release-7-7.1908.0.el7.centos.x86_64'.encode('utf-8')
        mock_isfile.return_value = True
        with open('argo-devel.repo', 'w') as f:
            f.write('test')

        files = self.repos5.create_file()
        mock_get_data.assert_called_once_with(include_internal=False)
        self.assertEqual(mock_mkdir.call_count, 2)
        mock_mkdir.assert_called_with('/tmp' + os.getcwd(), exist_ok=True)
        file1 = os.path.join(os.getcwd(), 'argo-devel.repo')
        file2 = os.path.join(os.getcwd(), 'nordugrid-updates.repo')
        self.assertEqual(mock_isfile.call_count, 2)
        mock_isfile.assert_has_calls(
            [mock.call(file1), mock.call(file2)], any_order=True
        )
        self.assertEqual(mock_copy.call_count, 2)
        mock_copy.assert_has_calls([
            mock.call(file1, '/tmp' + file1),
            mock.call(file2, '/tmp' + file2)
        ], any_order=True)
        self.assertEqual(files, [file1, file2])
        self.assertTrue(os.path.exists('argo-devel.repo'))
        self.assertTrue(os.path.exists('nordugrid-updates.repo'))

        with open('argo-devel.repo', 'r') as f:
            content1 = f.read()

        with open('nordugrid-updates.repo', 'r') as f:
            content2 = f.read()

        self.assertEqual(
            content1, mock_data['data']['argo-devel']['content']
        )
        self.assertEqual(
            content2, mock_data['data']['nordugrid-updates']['content']
        )

    @mock.patch('argo_poem_tools.repos.shutil.copyfile')
    @mock.patch('argo_poem_tools.repos.os.path.isfile')
    @mock.patch('argo_poem_tools.repos.os.makedirs')
    @mock.patch('argo_poem_tools.repos.subprocess.check_output')
    @mock.patch('argo_poem_tools.repos.YUMRepos.get_data')
    def test_do_not_override_file_which_already_exists_including_internal(
            self, mock_get_data, mock_sp, mock_mkdir, mock_isfile, mock_copy
    ):
        mock_get_data.return_value = mock_data["data"]
        mock_sp.return_value = \
            'centos-release-7-7.1908.0.el7.centos.x86_64'.encode('utf-8')
        mock_isfile.return_value = True
        with open('argo-devel.repo', 'w') as f:
            f.write('test')

        files = self.repos5.create_file(include_internal=True)
        mock_get_data.assert_called_once_with(include_internal=True)
        self.assertEqual(mock_mkdir.call_count, 2)
        mock_mkdir.assert_called_with('/tmp' + os.getcwd(), exist_ok=True)
        file1 = os.path.join(os.getcwd(), 'argo-devel.repo')
        file2 = os.path.join(os.getcwd(), 'nordugrid-updates.repo')
        self.assertEqual(mock_isfile.call_count, 2)
        mock_isfile.assert_has_calls(
            [mock.call(file1), mock.call(file2)], any_order=True
        )
        self.assertEqual(mock_copy.call_count, 2)
        mock_copy.assert_has_calls([
            mock.call(file1, '/tmp' + file1),
            mock.call(file2, '/tmp' + file2)
        ], any_order=True)
        self.assertEqual(files, [file1, file2])
        self.assertTrue(os.path.exists('argo-devel.repo'))
        self.assertTrue(os.path.exists('nordugrid-updates.repo'))

        with open('argo-devel.repo', 'r') as f:
            content1 = f.read()

        with open('nordugrid-updates.repo', 'r') as f:
            content2 = f.read()

        self.assertEqual(
            content1, mock_data['data']['argo-devel']['content']
        )
        self.assertEqual(
            content2, mock_data['data']['nordugrid-updates']['content']
        )

    @mock.patch('argo_poem_tools.repos.subprocess.call')
    @mock.patch('argo_poem_tools.repos.shutil.rmtree')
    @mock.patch('argo_poem_tools.repos.shutil.copy')
    @mock.patch('argo_poem_tools.repos.os.path.isfile')
    @mock.patch('argo_poem_tools.repos.os.listdir')
    @mock.patch('argo_poem_tools.repos.os.path.isdir')
    def test_clean(
            self, mock_isdir, mock_ls, mock_isfile, mock_cp, mock_rm, mock_call
    ):
        mock_isdir.return_value = True
        mock_ls.return_value = [
            'argo-devel.repo', 'nordugrid-updates.repo'
        ]
        mock_isfile.return_value = True
        file1 = os.path.join(os.getcwd(), 'argo-devel.repo')
        file2 = os.path.join(os.getcwd(), 'nordugrid-updates.repo')
        self.repos5.clean()
        self.assertEqual(mock_isdir.call_count, 1)
        mock_isdir.assert_called_with('/tmp' + os.getcwd())
        self.assertEqual(mock_ls.call_count, 1)
        mock_ls.assert_called_with('/tmp' + os.getcwd())
        self.assertEqual(mock_isfile.call_count, 2)
        mock_isfile.assert_has_calls([
            mock.call('/tmp' + file1),
            mock.call('/tmp' + file2)
        ], any_order=True)
        self.assertEqual(mock_cp.call_count, 2)
        mock_cp.assert_has_calls([
            mock.call('/tmp' + file1, os.getcwd()),
            mock.call('/tmp' + file2, os.getcwd())
        ], any_order=True)
        self.assertEqual(mock_rm.call_count, 1)
        mock_rm.assert_called_with('/tmp' + os.getcwd())
        self.assertEqual(mock_call.call_count, 1)
        mock_call.assert_called_with(['yum', 'clean', 'all'])

    @mock.patch('argo_poem_tools.repos.subprocess.call')
    @mock.patch('argo_poem_tools.repos.shutil.copy')
    @mock.patch('argo_poem_tools.repos.shutil.rmtree')
    def test_clean_if_override(self, mock_rmdir, mock_copy, mock_call):
        self.repos1.clean()
        self.assertEqual(mock_rmdir.call_count, 0)
        self.assertEqual(mock_copy.call_count, 0)
        self.assertEqual(mock_call.call_count, 1)
        mock_call.assert_called_with(['yum', 'clean', 'all'])
