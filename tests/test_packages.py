#!/usr/bin/python
import unittest

import mock
from argo_poem_tools.packages import Packages

data = {
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


def mock_func(*args, **kwargs):
    pass


class PackageTests(unittest.TestCase):
    def setUp(self):
        self.pkgs = Packages(data)

    def test_get_package_list(self):
        self.assertEqual(
            self.pkgs.package_list,
            [
                ('nordugrid-arc-nagios-plugins',),
                ('nagios-plugins-fedcloud', '0.5.0'),
                ('nagios-plugins-igtf', '1.4.0'),
                ('nagios-plugins-globus', '0.1.5')
            ]
        )

    @mock.patch('argo_poem_tools.packages.subprocess.check_call')
    @mock.patch('argo_poem_tools.packages.yum.YumBase.pkgSack')
    @mock.patch('argo_poem_tools.packages.yum.YumBase.rpmdb')
    def test_install_packages(self, mock_rpmdb, mock_yumdb, mock_sp):
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
        mock_rpmdb.returnPackages.return_value = [mock2, mock3, mock5]
        mock_yumdb.returnPackages.return_value = [
            mock1, mock2, mock3, mock4, mock5, mock6
        ]
        mock_sp.side_effect = mock_func
        info, warn = self.pkgs.install()
        self.assertEqual(mock_sp.call_count, 4)
        mock_sp.assert_has_calls([
            mock.call(
                ['yum', '-y', 'install', 'nagios-plugins-fedcloud-0.5.0']
            ),
            mock.call(['yum', '-y', 'downgrade', 'nagios-plugins-igtf-1.4.0']),
            mock.call(['yum', '-y', 'install', 'nagios-plugins-globus-0.1.5']),
            mock.call(['yum', '-y', 'install', 'nordugrid-arc-nagios-plugins'])
        ], any_order=True)
        self.assertEqual(
            info,
            [
                'Packages installed: nordugrid-arc-nagios-plugins',
                'Packages upgraded: '
                'nagios-plugins-fedcloud-0.4.0 -> '
                'nagios-plugins-fedcloud-0.5.0; nagios-plugins-globus-0.1.5',
                'Packages downgraded: '
                'nagios-plugins-igtf-1.5.0 -> nagios-plugins-igtf-1.4.0'
            ]
        )
        self.assertEqual(warn, [])

    @mock.patch('argo_poem_tools.packages.subprocess.check_call')
    @mock.patch('argo_poem_tools.packages.yum.YumBase.pkgSack')
    @mock.patch('argo_poem_tools.packages.yum.YumBase.rpmdb')
    def test_install_packages_if_installed_and_wrong_version_available(
            self, mock_rpmdb, mock_yumdb, mock_sp
    ):
        mock1 = mock.Mock(version='0.5.0')
        mock2 = mock.Mock(version='0.4.0')
        mock3 = mock.Mock(version='1.5.0')
        mock4 = mock.Mock(version='1.4.0')
        mock5 = mock.Mock(version='0.1.6')
        mock6 = mock.Mock(version='2.0.1')
        mock7 = mock.Mock(version='1.9.0')
        mock1.name = 'nagios-plugins-fedcloud'
        mock2.name = 'nagios-plugins-fedcloud'
        mock3.name = 'nagios-plugins-igtf'
        mock4.name = 'nagios-plugins-igtf'
        mock5.name = 'nagios-plugins-globus'
        mock6.name = 'nordugrid-arc-nagios-plugins'
        mock7.name = 'nordugrid-arc-nagios-plugins'
        mock_rpmdb.returnPackages.return_value = [mock2, mock3, mock7]
        mock_yumdb.returnPackages.return_value = [
            mock1, mock2, mock3, mock4, mock5, mock6
        ]
        mock_sp.side_effect = mock_func
        info, warn = self.pkgs.install()
        self.assertEqual(mock_sp.call_count, 4)
        mock_sp.assert_has_calls([
            mock.call(
                ['yum', '-y', 'install', 'nagios-plugins-fedcloud-0.5.0']
            ),
            mock.call(['yum', '-y', 'downgrade', 'nagios-plugins-igtf-1.4.0']),
            mock.call(['yum', '-y', 'install', 'nagios-plugins-globus-0.1.6']),
            mock.call(['yum', '-y', 'install', 'nordugrid-arc-nagios-plugins'])
        ], any_order=True)
        self.assertEqual(
            info,
            [
                'Packages upgraded: nordugrid-arc-nagios-plugins; '
                'nagios-plugins-fedcloud-0.4.0 -> nagios-plugins-fedcloud-'
                '0.5.0',
                'Packages downgraded: '
                'nagios-plugins-igtf-1.5.0 -> nagios-plugins-igtf-1.4.0',
                'Packages installed with different version: '
                'nagios-plugins-globus-0.1.5 -> nagios-plugins-globus-0.1.6'
            ]
        )
        self.assertEqual(warn, [])

    @mock.patch('argo_poem_tools.packages.subprocess.check_call')
    @mock.patch('argo_poem_tools.packages.yum.YumBase.pkgSack')
    @mock.patch('argo_poem_tools.packages.yum.YumBase.rpmdb')
    def test_install_if_exact_packages_not_found(
            self, mock_rpmdb, mock_yumdb, mock_sp
    ):
        mock1 = mock.Mock(version='2.0.0')
        mock2 = mock.Mock(version='0.6.0')
        mock3 = mock.Mock(version='1.4.0')
        mock4 = mock.Mock(version='0.8.0')
        mock5 = mock.Mock(version='0.1.5')
        mock6 = mock.Mock(version='0.7.0')
        mock1.name = 'nordugrid-arc-nagios-plugins'
        mock2.name = 'nagios-plugins-fedcloud'
        mock3.name = 'nagios-plugins-igtf'
        mock4.name = 'nagios-plugins-fedcloud'
        mock5.name = 'nagios-plugins-globus'
        mock6.name = 'nagios-plugins-fedcloud'
        mock_rpmdb.returnPackages.return_value = []
        mock_yumdb.returnPackages.return_value = [
            mock1, mock2, mock3, mock4, mock5, mock6
        ]
        mock_sp.side_effect = mock_func
        info, warn = self.pkgs.install()
        self.assertEqual(mock_sp.call_count, 4)
        mock_sp.assert_has_calls([
            mock.call(
                ['yum', '-y', 'install', 'nagios-plugins-fedcloud-0.8.0']
            ),
            mock.call(['yum', '-y', 'install', 'nagios-plugins-igtf-1.4.0']),
            mock.call(['yum', '-y', 'install', 'nagios-plugins-globus-0.1.5']),
            mock.call(['yum', '-y', 'install', 'nordugrid-arc-nagios-plugins'])
        ], any_order=True)
        self.assertEqual(
            info,
            [
                'Packages installed: nordugrid-arc-nagios-plugins; '
                'nagios-plugins-igtf-1.4.0; '
                'nagios-plugins-globus-0.1.5',
                'Packages installed with different version: '
                'nagios-plugins-fedcloud-0.5.0 -> nagios-plugins-fedcloud-0.8.0'
            ]
        )
        self.assertEqual(warn, [])

    @mock.patch('argo_poem_tools.packages.subprocess.check_call')
    @mock.patch('argo_poem_tools.packages.yum.YumBase.pkgSack')
    @mock.patch('argo_poem_tools.packages.yum.YumBase.rpmdb')
    def test_install_if_packages_not_found(
            self, mock_rpmdb, mock_yumbd, mock_sp
    ):
        mock1 = mock.Mock(version='0.6.0')
        mock2 = mock.Mock(version='1.4.0')
        mock1.name = 'nagios-plugins-fedcloud'
        mock2.name = 'nagios-plugins-igtf'
        mock_rpmdb.returnPackages.return_value = []
        mock_yumbd.returnPackages.return_value = [mock1, mock2]
        mock_sp.side_effect = mock_func
        info, warn = self.pkgs.install()
        self.assertEqual(mock_sp.call_count, 2)
        mock_sp.assert_has_calls([
            mock.call(
                ['yum', '-y', 'install', 'nagios-plugins-fedcloud-0.6.0']
            ),
            mock.call(['yum', '-y', 'install', 'nagios-plugins-igtf-1.4.0'])
        ], any_order=True)
        self.assertEqual(
            info,
            [
                'Packages installed: nagios-plugins-igtf-1.4.0',
                'Packages installed with different version: '
                'nagios-plugins-fedcloud-0.5.0 -> nagios-plugins-fedcloud-0.6.0'
            ]
        )
        self.assertEqual(
            warn,
            [
                'Packages not found: nordugrid-arc-nagios-plugins; '
                'nagios-plugins-globus-0.1.5'
            ]
        )

    @mock.patch('argo_poem_tools.packages.yum.YumBase.pkgSack')
    @mock.patch('argo_poem_tools.packages.yum.YumBase.rpmdb')
    def test_no_op_run(self, mock_rpmdb, mock_yumdb):
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
        mock_rpmdb.returnPackages.return_value = [mock2, mock3]
        mock_yumdb.returnPackages.return_value = [
            mock1, mock2, mock3, mock4, mock5, mock6
        ]
        info, warn = self.pkgs.no_op()
        self.assertEqual(
            info,
            [
                'Packages to be installed: nordugrid-arc-nagios-plugins; '
                'nagios-plugins-globus-0.1.5',
                'Packages to be upgraded: nagios-plugins-fedcloud-0.4.0 -> '
                'nagios-plugins-fedcloud-0.5.0',
                'Packages to be downgraded: '
                'nagios-plugins-igtf-1.5.0 -> nagios-plugins-igtf-1.4.0'
            ]
        )
        self.assertEqual(warn, [])

    @mock.patch('argo_poem_tools.packages.yum.YumBase.pkgSack')
    @mock.patch('argo_poem_tools.packages.yum.YumBase.rpmdb')
    def test_no_op_if_installed_and_wrong_version_available(
            self, mock_rpmdb, mock_yumdb
    ):
        mock1 = mock.Mock(version='0.5.0')
        mock2 = mock.Mock(version='0.4.0')
        mock3 = mock.Mock(version='1.5.0')
        mock4 = mock.Mock(version='1.4.0')
        mock5 = mock.Mock(version='0.1.6')
        mock6 = mock.Mock(version='2.0.1')
        mock7 = mock.Mock(version='1.9.0')
        mock1.name = 'nagios-plugins-fedcloud'
        mock2.name = 'nagios-plugins-fedcloud'
        mock3.name = 'nagios-plugins-igtf'
        mock4.name = 'nagios-plugins-igtf'
        mock5.name = 'nagios-plugins-globus'
        mock6.name = 'nordugrid-arc-nagios-plugins'
        mock7.name = 'nordugrid-arc-nagios-plugins'
        mock_rpmdb.returnPackages.return_value = [mock2, mock3, mock7]
        mock_yumdb.returnPackages.return_value = [
            mock1, mock2, mock3, mock4, mock5, mock6
        ]
        info, warn = self.pkgs.no_op()
        self.assertEqual(
            info,
            [
                'Packages to be upgraded: nordugrid-arc-nagios-plugins; '
                'nagios-plugins-fedcloud-0.4.0 -> nagios-plugins-fedcloud-'
                '0.5.0',
                'Packages to be downgraded: '
                'nagios-plugins-igtf-1.5.0 -> nagios-plugins-igtf-1.4.0',
                'Packages to be installed with different version: '
                'nagios-plugins-globus-0.1.5 -> nagios-plugins-globus-0.1.6'
            ]
        )
        self.assertEqual(warn, [])

    @mock.patch('argo_poem_tools.packages.yum.YumBase.pkgSack')
    @mock.patch('argo_poem_tools.packages.yum.YumBase.rpmdb')
    def test_no_op_exact_packages_not_found(self, mock_rpmdb, mock_yumdb):
        mock1 = mock.Mock(version='2.0.0')
        mock2 = mock.Mock(version='0.6.0')
        mock3 = mock.Mock(version='1.4.0')
        mock4 = mock.Mock(version='0.8.0')
        mock5 = mock.Mock(version='0.1.5')
        mock6 = mock.Mock(version='0.7.0')
        mock1.name = 'nordugrid-arc-nagios-plugins'
        mock2.name = 'nagios-plugins-fedcloud'
        mock3.name = 'nagios-plugins-igtf'
        mock4.name = 'nagios-plugins-fedcloud'
        mock5.name = 'nagios-plugins-globus'
        mock6.name = 'nagios-plugins-fedcloud'
        mock_rpmdb.returnPackages.return_value = []
        mock_yumdb.returnPackages.return_value = [
            mock1, mock2, mock3, mock4, mock5, mock6
        ]
        info, warn = self.pkgs.no_op()
        self.assertEqual(
            info,
            [
                'Packages to be installed: nordugrid-arc-nagios-plugins; '
                'nagios-plugins-igtf-1.4.0; '
                'nagios-plugins-globus-0.1.5',
                'Packages to be installed with different version: '
                'nagios-plugins-fedcloud-0.5.0 -> nagios-plugins-fedcloud-0.8.0'
            ]
        )
        self.assertEqual(warn, [])

    @mock.patch('argo_poem_tools.packages.yum.YumBase.pkgSack')
    @mock.patch('argo_poem_tools.packages.yum.YumBase.rpmdb')
    def test_no_op_if_packages_not_found(self, mock_rpmdb, mock_yumbd):
        mock1 = mock.Mock(version='0.6.0')
        mock2 = mock.Mock(version='1.4.0')
        mock1.name = 'nagios-plugins-fedcloud'
        mock2.name = 'nagios-plugins-igtf'
        mock_rpmdb.returnPackages.return_value = []
        mock_yumbd.returnPackages.return_value = [mock1, mock2]
        info, warn = self.pkgs.no_op()
        self.assertEqual(
            info,
            [
                'Packages to be installed: nagios-plugins-igtf-1.4.0',
                'Packages to be installed with different version: '
                'nagios-plugins-fedcloud-0.5.0 -> nagios-plugins-fedcloud-0.6.0'
            ]
        )
        self.assertEqual(
            warn,
            [
                'Packages not found: nordugrid-arc-nagios-plugins; '
                'nagios-plugins-globus-0.1.5'
            ]
        )


if __name__ == '__main__':
    unittest.main()
