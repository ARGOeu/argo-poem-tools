#!/usr/bin/python
import mock

from argo_poem_tools.packages import Packages

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
                    "version": "present"
                }
            ]
        }
    }
]


class PackageTests(unittest.TestCase):
    def setUp(self):
        self.pkgs = Packages(data)

    def test_get_package_list(self):
        self.assertEqual(
            self.pkgs.list_of_packages(),
            [
                ('nordugrid-arc-nagios-plugins',),
                ('nagios-plugins-fedcloud', '0.5.0'),
                ('nagios-plugins-igtf', '1.4.0'),
                ('nagios-plugins-globus', '0.1.5')
            ]
        )

    @mock.patch('yum.YumBase.pkgSack')
    @mock.patch('yum.YumBase.rpmdb')
    def test_get_packages(self, mock_yumbase1, mock_yumbase2):
        mock1 = mock.Mock(version='0.5.0')
        mock2 = mock.Mock(version='0.4.0')
        mock3 = mock.Mock(version='1.5.0')
        mock4 = mock.Mock(version='1.4.0')
        mock5 = mock.Mock(version='0.1.5')
        mock6 = mock.Mock(version='2.0.0')
        mock1.name = 'nagios-plugins-fedcloud'
        mock2.name = 'nagios-plugins-fedcloud'
        mock3.name = 'nagios-plugins-igtf'
        mock4.name = 'nagios-plugins-igtf'
        mock5.name = 'nagios-plugins-globus'
        mock6.name = 'nordugrid-arc-nagios-plugins'
        mock_yumbase1.returnPackages.return_value = [mock2, mock3]
        mock_yumbase2.returnPackages.return_value = [
            mock1, mock2, mock3, mock4, mock5, mock6
        ]

        install, downgrade = self.pkgs.get_packages()

        self.assertEqual(
            install,
            [
                'nordugrid-arc-nagios-plugins',
                'nagios-plugins-fedcloud-0.5.0',
                'nagios-plugins-globus-0.1.5'
             ]
        )
        self.assertEqual(downgrade, ['nagios-plugins-igtf-1.4.0'])

    @mock.patch('yum.YumBase.pkgSack')
    @mock.patch('yum.YumBase.rpmdb')
    def test_get_packages_if_installed_and_wrong_version_available(
            self, mock_yumbase1, mock_yumbase2
    ):
        mock1 = mock.Mock(version='0.5.0')
        mock2 = mock.Mock(version='0.4.0')
        mock3 = mock.Mock(version='1.5.0')
        mock4 = mock.Mock(version='1.4.0')
        mock5 = mock.Mock(version='0.1.5')
        mock6 = mock.Mock(version='2.0.1')
        mock7 = mock.Mock(version='1.9.0')
        mock1.name = 'nagios-plugins-fedcloud'
        mock2.name = 'nagios-plugins-fedcloud'
        mock3.name = 'nagios-plugins-igtf'
        mock4.name = 'nagios-plugins-igtf'
        mock5.name = 'nagios-plugins-globus'
        mock6.name = 'nordugrid-arc-nagios-plugins'
        mock7.name = 'nordugrid-arc-nagios-plugins'
        mock_yumbase1.returnPackages.return_value = [mock2, mock3, mock7]
        mock_yumbase2.returnPackages.return_value = [
            mock1, mock2, mock3, mock4, mock5, mock6
        ]

        install, downgrade = self.pkgs.get_packages()

        self.assertEqual(
            install,
            ['nagios-plugins-fedcloud-0.5.0',
             'nagios-plugins-globus-0.1.5']
        )
        self.assertEqual(downgrade, ['nagios-plugins-igtf-1.4.0'])

    @mock.patch('yum.YumBase.pkgSack')
    def test_exact_packages_not_found(self, mock_yumbase):
        mock1 = mock.Mock(version='2.0.0')
        mock2 = mock.Mock(version='0.6.0')
        mock3 = mock.Mock(version='1.4.0')
        mock1.name = 'nordugrid-arc-nagios-plugins'
        mock2.name = 'nagios-plugins-fedcloud'
        mock3.name = 'nagios-plugins-igtf'
        mock_yumbase.returnPackages.return_value = [mock1, mock2, mock3]

        self.assertEqual(
            self.pkgs.exact_packages_not_found(),
            [
                ('nagios-plugins-fedcloud', '0.5.0'),
                ('nagios-plugins-globus', '0.1.5')
            ]
        )

    @mock.patch('yum.YumBase.pkgSack')
    def test_packages_not_found(self, mock_yumbase):
        mock1 = mock.Mock(version='2.0.0')
        mock2 = mock.Mock(version='0.6.0')
        mock3 = mock.Mock(version='1.4.0')
        mock1.name = 'nordugrid-arc-nagios-plugins'
        mock2.name = 'nagios-plugins-fedcloud'
        mock3.name = 'nagios-plugins-igtf'
        mock_yumbase.returnPackages.return_value = [mock1, mock2, mock3]

        self.assertEqual(
            self.pkgs.packages_not_found(),
            [('nagios-plugins-globus', '0.1.5')]
        )

    @mock.patch('yum.YumBase.pkgSack')
    def test_get_packages_not_found(self, mock_yumbase):
        mock1 = mock.Mock(version='0.6.0')
        mock2 = mock.Mock(version='1.4.0')
        mock1.name = 'nagios-plugins-fedcloud'
        mock2.name = 'nagios-plugins-igtf'
        mock_yumbase.returnPackages.return_value = [mock1, mock2]

        self.assertEqual(
            self.pkgs.get_packages_not_found(),
            ['nordugrid-arc-nagios-plugins', 'nagios-plugins-globus-0.1.5']
        )

    @mock.patch('yum.YumBase.pkgSack')
    def test_packages_found_with_different_version(self, mock_yumbase):
        mock1 = mock.Mock(version='2.0.0')
        mock2 = mock.Mock(version='0.5.0')
        mock3 = mock.Mock(version='1.5.0')
        mock1.name = 'nordugrid-arc-nagios-plugins'
        mock2.name = 'nagios-plugins-fedcloud'
        mock3.name = 'nagios-plugins-igtf'
        mock_yumbase.returnPackages.return_value = [mock1, mock2, mock3]

        self.assertEqual(
            self.pkgs.packages_found_with_different_version(),
            [('nagios-plugins-igtf', '1.5.0')]
        )

    @mock.patch('yum.YumBase.pkgSack')
    def test_get_packages_installed_with_different_version(self, mock_yumbase):
        mock1 = mock.Mock(version='2.0.0')
        mock2 = mock.Mock(version='0.5.0')
        mock3 = mock.Mock(version='1.5.0')
        mock1.name = 'nordugrid-arc-nagios-plugins'
        mock2.name = 'nagios-plugins-fedcloud'
        mock3.name = 'nagios-plugins-igtf'
        mock_yumbase.returnPackages.return_value = [mock1, mock2, mock3]

        self.assertEqual(
            self.pkgs.get_packages_installed_with_different_version(),
            ['nagios-plugins-igtf-1.4.0 -> nagios-plugins-igtf-1.5.0']
        )

    @mock.patch('yum.YumBase.pkgSack')
    def test_get_packages_installed_with_version_as_requested(
            self, mock_yumbase
    ):
        mock1 = mock.Mock(version='2.0.0')
        mock2 = mock.Mock(version='0.5.0')
        mock3 = mock.Mock(version='1.5.0')
        mock1.name = 'nordugrid-arc-nagios-plugins'
        mock2.name = 'nagios-plugins-fedcloud'
        mock3.name = 'nagios-plugins-igtf'
        mock_yumbase.returnPackages.return_value = [mock1, mock2, mock3]

        self.assertEqual(
            self.pkgs.get_packages_installed_with_versions_as_requested(
                [
                    'nordugrid-arc-nagios-plugins',
                    'nagios-plugins-fedcloud-0.5.0',
                    'nagios-plugins-igtf'
                ]
            ),
            [
                'nordugrid-arc-nagios-plugins',
                'nagios-plugins-fedcloud-0.5.0'
            ]
        )


if __name__ == '__main__':
    unittest.main()
