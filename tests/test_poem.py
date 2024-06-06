import unittest
from unittest import mock

from argo_poem_tools.exceptions import POEMException
from argo_poem_tools.poem import POEM, merge_tenants_data

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
        "nagios-plugins-egi-notebooks (0.2.3)"
    ]
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

OS_RELEASE_EL7 = \
    b'NAME="CentOS Linux"\n' \
    b'VERSION="7 (Core)"\n' \
    b'ID="centos"\n' \
    b'ID_LIKE="rhel fedora"\n' \
    b'VERSION_ID="7"\n' \
    b'PRETTY_NAME="CentOS Linux 7 (Core)"\n' \
    b'ANSI_COLOR="0;31"\n' \
    b'CPE_NAME="cpe:/o:centos:centos:7"\n' \
    b'HOME_URL="https://www.centos.org/"\n' \
    b'BUG_REPORT_URL="https://bugs.centos.org/"\n\n' \
    b'CENTOS_MANTISBT_PROJECT="CentOS-7"\n' \
    b'CENTOS_MANTISBT_PROJECT_VERSION="7"\n' \
    b'REDHAT_SUPPORT_PRODUCT="centos"\n' \
    b'REDHAT_SUPPORT_PRODUCT_VERSION="7"\n\n'

OS_RELEASE_EL9 = \
    b'NAME="Rocky Linux"\n' \
    b'VERSION="9.1 (Blue Onyx)"\n' \
    b'ID="rocky"\n' \
    b'ID_LIKE="rhel centos fedora"\n' \
    b'VERSION_ID="9.1"\n' \
    b'PLATFORM_ID="platform:el9"\n' \
    b'PRETTY_NAME="Rocky Linux 9.1 (Blue Onyx)"\n' \
    b'ANSI_COLOR="0;32"\n' \
    b'LOGO="fedora-logo-icon"\n' \
    b'CPE_NAME="cpe:/o:rocky:rocky:9::baseos"\n' \
    b'HOME_URL="https://rockylinux.org/"\n' \
    b'BUG_REPORT_URL="https://bugs.rockylinux.org/"\n' \
    b'ROCKY_SUPPORT_PRODUCT="Rocky-Linux-9"\n' \
    b'ROCKY_SUPPORT_PRODUCT_VERSION="9.1"\n' \
    b'REDHAT_SUPPORT_PRODUCT="Rocky Linux"\n' \
    b'REDHAT_SUPPORT_PRODUCT_VERSION="9.1"\n'


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


class MergeDataTests(unittest.TestCase):
    def test_merge_data(self):
        data = {
            "tenant1": {
                "argo": {
                    "content": "[argo-devel]\n"
                               "name=ARGO Product Repository\n"
                               "baseurl=http://rpm-repo.argo.grnet.gr/ARGO/"
                               "devel/rocky9/\n"
                               "gpgcheck=0\n"
                               "enabled=1\n"
                               "priority=99\n"
                               "exclude=\n"
                               "includepkgs=",
                    "packages": [
                        {
                            "name": "argo-probe-argo-tools",
                            "version": "0.2.0"
                        },
                        {
                            "name": "argo-probe-cert",
                            "version": "2.0.1"
                        },
                        {
                            "name": "argo-probe-ams",
                            "version": "present"
                        },
                        {
                            "name": "argo-probe-poem",
                            "version": "present"
                        }
                    ]
                },
                "epel": {
                    "content": "[epel]\nname=Extra Packages for Enterprise "
                               "Linux 9 - $basearch\n#baseurl="
                               "http://download.fedoraproject.org/pub/epel"
                               "/9/$basearch\n"
                               "mirrorlist=https://mirrors.fedoraproject.org/"
                               "metalink?repo=epel-9&arch=$basearch\n"
                               "failovermethod=priority\n"
                               "enabled=1\n"
                               "gpgcheck=1\n"
                               "gpgkey=https://dl.fedoraproject.org/pub/epel"
                               "/RPM-GPG-KEY-EPEL-7\n"
                               "priority=11",
                    "packages": [
                        {
                            "name": "nagios-plugins-http",
                            "version": "present"
                        },
                        {
                            "name": "nagios-plugins-disk",
                            "version": "present"
                        },
                        {
                            "name": "nagios-plugins-procs",
                            "version": "present"
                        }
                    ]
                },
                "missing_packages": [
                    "argo-probe-grnet-agora (0.4)",
                    "nagios-plugins-egi-notebooks (0.2.3)"
                ]
            },
            "tenant2": {
                "argo": {
                    "content": "[argo-devel]\n"
                               "name=ARGO Product Repository\n"
                               "baseurl=http://rpm-repo.argo.grnet.gr/ARGO/"
                               "devel/rocky9/\n"
                               "gpgcheck=0\n"
                               "enabled=1\n"
                               "priority=99\n"
                               "exclude=\n"
                               "includepkgs=",
                    "packages": [
                        {
                            "name": "argo-probe-igtf",
                            "version": "2.1.0"
                        },
                        {
                            "name": "argo-probe-cert",
                            "version": "2.0.1"
                        },
                        {
                            "name": "argo-probe-ams-publisher",
                            "version": "present"
                        },
                        {
                            "name": "argo-probe-poem",
                            "version": "present"
                        }
                    ]
                },
                "epel": {
                    "content": "[epel]\nname=Extra Packages for Enterprise "
                               "Linux 9 - $basearch\n#baseurl="
                               "http://download.fedoraproject.org/pub/epel"
                               "/9/$basearch\n"
                               "mirrorlist=https://mirrors.fedoraproject.org/"
                               "metalink?repo=epel-9&arch=$basearch\n"
                               "failovermethod=priority\n"
                               "enabled=1\n"
                               "gpgcheck=1\n"
                               "gpgkey=https://dl.fedoraproject.org/pub/epel"
                               "/RPM-GPG-KEY-EPEL-7\n"
                               "priority=11",
                    "packages": [
                        {
                            "name": "nagios-plugins-dummy",
                            "version": "present"
                        },
                        {
                            "name": "nagios-plugins-procs",
                            "version": "present"
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
                },
                "missing_packages": [
                    "nagios-plugins-bdii (1.0.14)",
                    "nagios-plugins-egi-notebooks (0.2.3)"
                ]
            }
        }

        merged_data = merge_tenants_data(data=data)
        self.assertEqual(
            merged_data, {
                "argo": {
                    "content": "[argo-devel]\n"
                               "name=ARGO Product Repository\n"
                               "baseurl=http://rpm-repo.argo.grnet.gr/ARGO/"
                               "devel/rocky9/\n"
                               "gpgcheck=0\n"
                               "enabled=1\n"
                               "priority=99\n"
                               "exclude=\n"
                               "includepkgs=",
                    "packages": [
                        {
                            "name": "argo-probe-ams",
                            "version": "present"
                        },
                        {
                            "name": "argo-probe-ams-publisher",
                            "version": "present"
                        },
                        {
                            "name": "argo-probe-argo-tools",
                            "version": "0.2.0"
                        },
                        {
                            "name": "argo-probe-cert",
                            "version": "2.0.1"
                        },
                        {
                            "name": "argo-probe-igtf",
                            "version": "2.1.0"
                        },
                        {
                            "name": "argo-probe-poem",
                            "version": "present"
                        }
                    ]
                },
                "epel": {
                    "content": "[epel]\nname=Extra Packages for Enterprise "
                               "Linux 9 - $basearch\n#baseurl="
                               "http://download.fedoraproject.org/pub/epel"
                               "/9/$basearch\n"
                               "mirrorlist=https://mirrors.fedoraproject.org/"
                               "metalink?repo=epel-9&arch=$basearch\n"
                               "failovermethod=priority\n"
                               "enabled=1\n"
                               "gpgcheck=1\n"
                               "gpgkey=https://dl.fedoraproject.org/pub/epel"
                               "/RPM-GPG-KEY-EPEL-7\n"
                               "priority=11",
                    "packages": [
                        {
                            "name": "nagios-plugins-disk",
                            "version": "present"
                        },
                        {
                            "name": "nagios-plugins-dummy",
                            "version": "present"
                        },
                        {
                            "name": "nagios-plugins-http",
                            "version": "present"
                        },
                        {
                            "name": "nagios-plugins-procs",
                            "version": "present"
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
                },
                "missing_packages": [
                    "argo-probe-grnet-agora (0.4)",
                    "nagios-plugins-bdii (1.0.14)",
                    "nagios-plugins-egi-notebooks (0.2.3)"
                ]
            }
        )


class POEMTests(unittest.TestCase):
    def setUp(self):
        self.poem1 = POEM(
            hostname='mock.url.com',
            token='some-token-1234',
            profiles=['TEST_PROFILE1', 'TEST_PROFILE2']
        )
        self.poem2 = POEM(
            hostname='http://mock.url.com/',
            token='some-token-1234',
            profiles=['TEST_PROFILE1']
        )
        self.poem3 = POEM(
            hostname='https://mock.url.com/',
            token='some-token-1234',
            profiles=['TEST_PROFILE1', 'TEST_PROFILE2']
        )
        self.poem4 = POEM(
            hostname='mock.url.com',
            token='some-token-1234',
            profiles=''
        )
        self.poem5 = POEM(
            hostname='mock.url.com',
            token='some-token-1234',
            profiles=['TEST_PROFILE1', 'TEST_PROFILE2']
        )

    @mock.patch('argo_poem_tools.poem.subprocess.check_output')
    @mock.patch('argo_poem_tools.poem.requests.get')
    def test_get_data_el7(self, mock_request, mock_sp):
        mock_request.side_effect = mock_request_ok
        mock_sp.return_value = OS_RELEASE_EL7
        data = self.poem1.get_data()
        mock_request.assert_called_once_with(
            'https://mock.url.com/api/v2/repos/centos7',
            headers={'x-api-key': 'some-token-1234',
                     'profiles': '[TEST_PROFILE1, TEST_PROFILE2]'},
            timeout=180
        )
        self.assertEqual(data, mock_data['data'])
        self.assertEqual(
            self.poem1.missing_packages,
            [
                'nagios-plugins-bdii (1.0.14)',
                'nagios-plugins-egi-notebooks (0.2.3)'
            ]
        )

    @mock.patch('argo_poem_tools.poem.subprocess.check_output')
    @mock.patch('argo_poem_tools.poem.requests.get')
    def test_get_data_el9(self, mock_request, mock_sp):
        mock_request.side_effect = mock_request_ok
        mock_sp.return_value = OS_RELEASE_EL9
        data = self.poem1.get_data()
        mock_request.assert_called_once_with(
            'https://mock.url.com/api/v2/repos/rocky9',
            headers={'x-api-key': 'some-token-1234',
                     'profiles': '[TEST_PROFILE1, TEST_PROFILE2]'},
            timeout=180
        )
        self.assertEqual(data, mock_data['data'])
        self.assertEqual(
            self.poem1.missing_packages,
            [
                'nagios-plugins-bdii (1.0.14)',
                'nagios-plugins-egi-notebooks (0.2.3)'
            ]
        )

    @mock.patch('argo_poem_tools.poem.subprocess.check_output')
    @mock.patch('argo_poem_tools.poem.requests.get')
    def test_get_data_including_internal_metrics(self, mock_request, mock_sp):
        mock_request.side_effect = mock_request_ok
        mock_sp.return_value = OS_RELEASE_EL9
        data = self.poem1.get_data(include_internal=True)
        self.assertEqual(mock_request.call_count, 2)
        mock_request.assert_has_calls([
            mock.call(
                "https://mock.url.com/api/v2/repos/rocky9",
                headers={'x-api-key': 'some-token-1234',
                         'profiles': '[TEST_PROFILE1, TEST_PROFILE2]'},
                timeout=180
            ),
            mock.call(
                "https://mock.url.com/api/v2/repos_internal/rocky9",
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
            self.poem1.missing_packages,
            [
                'nagios-plugins-bdii (1.0.14)',
                'nagios-plugins-egi-notebooks (0.2.3)'
            ]
        )

    @mock.patch('argo_poem_tools.poem.subprocess.check_output')
    @mock.patch('argo_poem_tools.poem.requests.get')
    def test_get_data_if_hostname_http(self, mock_request, mock_sp):
        mock_request.side_effect = mock_request_ok
        mock_sp.return_value = OS_RELEASE_EL9
        data = self.poem2.get_data()
        mock_request.assert_called_once_with(
            'https://mock.url.com/api/v2/repos/rocky9',
            headers={'x-api-key': 'some-token-1234',
                     'profiles': '[TEST_PROFILE1]'},
            timeout=180
        )
        self.assertEqual(data, mock_data['data'])
        self.assertEqual(
            self.poem2.missing_packages,
            [
                'nagios-plugins-bdii (1.0.14)',
                'nagios-plugins-egi-notebooks (0.2.3)'
            ]
        )

    @mock.patch('argo_poem_tools.poem.subprocess.check_output')
    @mock.patch('argo_poem_tools.poem.requests.get')
    def test_get_data_if_hostname_http_including_internal(
            self, mock_request, mock_sp
    ):
        mock_request.side_effect = mock_request_ok
        mock_sp.return_value = OS_RELEASE_EL9
        data = self.poem2.get_data(include_internal=True)
        mock_request.assert_has_calls([
            mock.call(
                "https://mock.url.com/api/v2/repos/rocky9",
                headers={'x-api-key': 'some-token-1234',
                         'profiles': '[TEST_PROFILE1]'},
                timeout=180
            ),
            mock.call(
                "https://mock.url.com/api/v2/repos_internal/rocky9",
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
            self.poem2.missing_packages,
            [
                'nagios-plugins-bdii (1.0.14)',
                'nagios-plugins-egi-notebooks (0.2.3)'
            ]
        )

    @mock.patch('argo_poem_tools.poem.subprocess.check_output')
    @mock.patch('argo_poem_tools.poem.requests.get')
    def test_get_data_if_hostname_https(self, mock_request, mock_sp):
        mock_request.side_effect = mock_request_ok
        mock_sp.return_value = OS_RELEASE_EL9
        data = self.poem3.get_data()
        mock_request.assert_called_once_with(
            'https://mock.url.com/api/v2/repos/rocky9',
            headers={'x-api-key': 'some-token-1234',
                     'profiles': '[TEST_PROFILE1, TEST_PROFILE2]'},
            timeout=180
        )
        self.assertEqual(data, mock_data['data'])
        self.assertEqual(
            self.poem3.missing_packages,
            [
                'nagios-plugins-bdii (1.0.14)',
                'nagios-plugins-egi-notebooks (0.2.3)'
            ]
        )

    @mock.patch('argo_poem_tools.poem.subprocess.check_output')
    @mock.patch('argo_poem_tools.poem.requests.get')
    def test_get_data_if_hostname_https_including_internal(
            self, mock_request, mock_sp
    ):
        mock_request.side_effect = mock_request_ok
        mock_sp.return_value = OS_RELEASE_EL9
        data = self.poem3.get_data(include_internal=True)
        mock_request.assert_has_calls([
            mock.call(
                "https://mock.url.com/api/v2/repos/rocky9",
                headers={'x-api-key': 'some-token-1234',
                         'profiles': '[TEST_PROFILE1, TEST_PROFILE2]'},
                timeout=180
            ),
            mock.call(
                "https://mock.url.com/api/v2/repos_internal/rocky9",
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
            self.poem3.missing_packages,
            [
                'nagios-plugins-bdii (1.0.14)',
                'nagios-plugins-egi-notebooks (0.2.3)'
            ]
        )

    @mock.patch('argo_poem_tools.poem.subprocess.check_output')
    @mock.patch('argo_poem_tools.poem.requests.get')
    def test_get_data_if_server_error(self, mock_request, mock_sp):
        mock_request.side_effect = mock_request_server_error
        mock_sp.return_value = OS_RELEASE_EL9
        with self.assertRaises(POEMException) as err:
            self.poem1.get_data()
        self.assertEqual(
            err.exception.__str__(),
            "Error fetching YUM repos: 500 Server Error"
        )

    @mock.patch('argo_poem_tools.poem.subprocess.check_output')
    @mock.patch('argo_poem_tools.poem.requests.get')
    def test_get_data_if_server_error_including_internal(
            self, mock_request, mock_sp
    ):
        mock_request.side_effect = mock_request_server_error
        mock_sp.return_value = OS_RELEASE_EL9
        with self.assertRaises(POEMException) as err:
            self.poem1.get_data(include_internal=True)
        self.assertEqual(
            err.exception.__str__(),
            "Error fetching YUM repos: 500 Server Error"
        )

    @mock.patch('argo_poem_tools.poem.subprocess.check_output')
    @mock.patch('argo_poem_tools.poem.requests.get')
    def test_get_data_if_wrong_url(self, mock_request, mock_sp):
        mock_request.side_effect = mock_request_wrong_url
        mock_sp.return_value = OS_RELEASE_EL9
        with self.assertRaises(POEMException) as err:
            self.poem1.get_data()
        self.assertEqual(
            err.exception.__str__(),
            "Error fetching YUM repos: 404 Not Found"
        )

    @mock.patch('argo_poem_tools.poem.subprocess.check_output')
    @mock.patch('argo_poem_tools.poem.requests.get')
    def test_get_data_if_wrong_token(self, mock_request, mock_sp):
        mock_request.side_effect = mock_request_wrong_token
        mock_sp.return_value = OS_RELEASE_EL9
        with self.assertRaises(POEMException) as err:
            self.poem1.get_data()
        self.assertEqual(
            err.exception.__str__(),
            "Error fetching YUM repos: 403 Forbidden: "
            "Authentication credentials were not provided."
        )

    @mock.patch('argo_poem_tools.poem.subprocess.check_output')
    @mock.patch('argo_poem_tools.poem.requests.get')
    def test_get_data_if_no_profiles(self, mock_request, mock_sp):
        mock_request.side_effect = mock_request_wrong_profiles
        mock_sp.return_value = OS_RELEASE_EL9
        with self.assertRaises(POEMException) as err:
            self.poem1.get_data()
        self.assertEqual(
            err.exception.__str__(),
            "Error fetching YUM repos: 400 Bad Request: "
            "You must define profile!"
        )

    @mock.patch('argo_poem_tools.poem.subprocess.check_output')
    @mock.patch('argo_poem_tools.poem.requests.get')
    def test_get_data_if_json_without_details(
            self, mock_request, mock_sp
    ):
        mock_request.side_effect = mock_request_json_without_details_key
        mock_sp.return_value = OS_RELEASE_EL9
        with self.assertRaises(POEMException) as err:
            self.poem1.get_data()
        self.assertEqual(
            err.exception.__str__(),
            "Error fetching YUM repos: 400 Bad Request"
        )
