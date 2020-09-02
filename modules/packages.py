import subprocess

import rpm
import yum


def _pop_arch(pkg_string):
    pkg_string_split = pkg_string.split('.')
    pkg = '.'.join(pkg_string_split[:-1])
    return pkg


class Packages:
    def __init__(self, data):
        self.data = data
        self.yb = yum.YumBase()
        self.package_list = self._list()
        self.packages_different_version = None
        self.packages_not_found = None
        self.available_packages = None

    def _list(self):
        list_packages = []
        for key, value in self.data.items():
            for item in value['packages']:
                if item['version'] == 'present':
                    list_packages.append((item['name'],))
                else:
                    list_packages.append((item['name'], item['version']))

        return list_packages

    @staticmethod
    def _get_available_packages():
        output = subprocess.check_output(['yum', 'list', 'available'])
        output_list = output.decode('utf-8').split('\n')
        pkg_index = output_list.index('Available Packages') + 1
        pkgs = output_list[pkg_index:]

        formatted_pkgs = []
        for pkg in pkgs:
            pkg_list = list(filter(None, pkg.split(' ')))
            if pkg_list:
                pkg_list_split = pkg_list[1].split('-')
                version = pkg_list_split[0]
                release = pkg_list_split[1]
                formatted_pkgs.append(
                    dict(
                        name=_pop_arch(pkg_list[0]),
                        version=version,
                        release=release
                    )
                )

        return formatted_pkgs

    def _get_exceptions(self):
        """
        Go through packages available from YUM repo, and determine which one of
        them are found with different version and which one are not found at
        all.
        """
        pkgs = self.yb.pkgSack.returnPackages()
        self.available_packages = [
            (pkg.name, pkg.version, pkg.release) for pkg in pkgs
        ]
        available_vr = [(pkg.name, pkg.version) for pkg in pkgs]

        wrong_version = []
        not_found = []
        for item in self.package_list:
            if len(item) > 1 and item not in available_vr and \
                    item[0] in [a[0] for a in self.available_packages]:
                avail_versions = \
                    [a for a in self.available_packages if a[0] == item[0]]
                if len(avail_versions) > 1:
                    max_version = avail_versions[0]
                    for version in avail_versions:
                        if rpm.labelCompare(
                                ('mock', version[1], 'mock'),
                                ('mock', max_version[1], 'mock')
                        ) > 0:
                            max_version = version

                    wrong_version.append(max_version)

                else:
                    wrong_version.append(
                        [(a[0], a[1]) for a in self.available_packages if
                         a[0] == item[0]][0]
                    )

            if item[0] not in [a[0] for a in self.available_packages]:
                not_found.append(item)

        self.packages_different_version = wrong_version
        self.packages_not_found = not_found

    @staticmethod
    def _get_max_verson(available_packages):
        max_version = available_packages[0]
        for version in available_packages:
            if rpm.labelCompare(
                    ('mock', version[1], version[2]),
                    ('mock', max_version[1], max_version[2])
            ) > 0:
                max_version = version

        return max_version

    def _get(self):
        if not self.packages_different_version:
            self._get_exceptions()

        pkgs = self.yb.rpmdb.returnPackages()
        installed_packages = [
            (pkg.name, pkg.version, pkg.release) for pkg in pkgs
        ]

        # list of installed packages' name
        installed_names = [pkg[0] for pkg in installed_packages]

        # list of packages which are available with different version
        diff_versions_names = [p[0] for p in self.packages_different_version]

        # list of packages which are available in repos (both name and version)
        installable_packages = [
            pkg for pkg in self.package_list if
            pkg not in self.packages_not_found and
            pkg[0] not in diff_versions_names
        ]

        install = []
        upgrade = []
        downgrade = []
        for item in installable_packages:
            if item[0] in installed_names:
                installed_ver = installed_packages[
                    installed_names.index(item[0])
                ][1]
                installed_release = installed_packages[
                    installed_names.index(item[0])
                ][2]

                # all the available packages with the given name and version
                if len(item) > 1:
                    available_items = [
                        pkg for pkg in self.available_packages
                        if item[0] == pkg[0] and item[1] == pkg[1]
                    ]

                else:
                    available_items = [
                        pkg for pkg in self.available_packages
                        if item[0] == pkg[0]
                    ]

                max_version = self._get_max_verson(available_items)

                if len(item) > 1:
                    if item[1] == installed_ver:
                        change_tuple = ('-'.join(item),)
                    else:
                        change_tuple = (
                            item[0] + '-' + installed_ver, '-'.join(item)
                        )

                else:
                    change_tuple = item

                if rpm.labelCompare(
                        ('mock', max_version[1], max_version[2]),
                        ('mock', installed_ver, installed_release)
                ) > 0:
                    upgrade.append(change_tuple)

                elif rpm.labelCompare(
                        ('mock', max_version[1], max_version[2]),
                        ('mock', installed_ver, installed_release)
                ) < 0:
                    downgrade.append(change_tuple)

                else:
                    continue

            else:
                if len(item) == 2:
                    install.append('-'.join(item))
                else:
                    install.append(item[0])

        diff_ver = []
        for item in self.packages_different_version:
            orig_item = self.package_list[
                [p[0] for p in self.package_list].index(item[0])
            ]

            if item[0] in installed_names:
                installed_ver = installed_packages[
                    installed_names.index(item[0])
                ][1]
                installed_release = installed_packages[
                    installed_names.index(item[0])
                ][2]

                available_items = [
                    pkg for pkg in self.available_packages if
                    item[0] == pkg[0]
                ]

                max_version = self._get_max_verson(available_items)

                if rpm.labelCompare(
                        ('mock', max_version[1], max_version[2]),
                        ('mock', installed_ver, installed_release)
                ) > 0:
                    if max_version[1] != installed_ver:
                        diff_ver.append(
                            ('-'.join(orig_item), '{}-{}'.format(
                                item[0], max_version[1])
                             )
                        )

            else:
                diff_ver.append(('-'.join(orig_item), '-'.join(item[0:2])))

        not_found = []
        for item in self.packages_not_found:
            if len(item) > 1:
                not_found.append('-'.join(item))
            else:
                not_found.append(item[0])

        return install, upgrade, downgrade, diff_ver, not_found

    def install(self):
        install, upgrade, downgrade, diff_ver, not_found = self._get()
        installed = []
        not_installed = []
        upgraded = []
        not_upgraded = []
        downgraded = []
        not_downgraded = []
        installed_diff_ver = []
        not_installed_diff_ver = []
        if install:
            for pkg in install:
                try:
                    subprocess.check_call(['yum', '-y', 'install', pkg])
                    installed.append(pkg)

                except subprocess.CalledProcessError:
                    not_installed.append(pkg)

        if upgrade:
            for pkg in upgrade:
                try:
                    if len(pkg) == 2:
                        subprocess.check_call(['yum', '-y', 'install', pkg[1]])
                        upgraded.append(' -> '.join(pkg))
                    else:
                        subprocess.check_call(['yum', '-y', 'install', pkg[0]])
                        upgraded.append(pkg[0])

                except subprocess.CalledProcessError:
                    not_upgraded.append(pkg[0])

        if downgrade:
            for pkg in downgrade:
                try:
                    subprocess.check_call(['yum', '-y', 'downgrade', pkg[1]])
                    downgraded.append(' -> '.join(pkg))

                except subprocess.CalledProcessError:
                    not_downgraded.append(pkg[0])

        if diff_ver:
            for pkg in diff_ver:
                try:
                    subprocess.check_call(['yum', '-y', 'install', pkg[1]])
                    installed_diff_ver.append(' -> '.join(pkg))

                except subprocess.CalledProcessError:
                    not_installed_diff_ver.append(pkg[0])

        info_msg = []
        warn_msg = []
        if installed:
            info_msg.append('Packages installed: ' + '; '.join(installed))

        if upgraded:
            info_msg.append('Packages upgraded: ' + '; '.join(upgraded))

        if downgraded:
            info_msg.append('Packages downgraded: ' + '; '.join(downgraded))

        if installed_diff_ver:
            info_msg.append(
                'Packages installed with different version: ' + '; '.join(
                    installed_diff_ver
                )
            )

        if not_installed:
            warn_msg.append(
                'Packages not installed: ' + '; '.join(not_installed)
            )

        if not_upgraded:
            warn_msg.append(
                'Packages not upgraded: ' + '; '.join(not_upgraded)
            )

        if not_downgraded:
            warn_msg.append(
                'Packages not downgraded: ' + '; '.join(not_downgraded)
            )

        if not_installed_diff_ver:
            warn_msg.append(
                'Packages not installed: ' + '; '.join(not_installed_diff_ver)
            )

        if not_found:
            warn_msg.append(
                'Packages not found: ' + '; '.join(not_found)
            )

        return info_msg, warn_msg

    def no_op(self):
        install, upgrade0, downgrade0, diff_ver0, not_found = self._get()
        info_msg = []
        warn_msg = []

        if install:
            info_msg.append(
                'Packages to be installed: ' + '; '.join(install)
            )

        if upgrade0:
            upgrade = []
            for item in upgrade0:
                if len(item) > 1:
                    upgrade.append(' -> '.join(item))
                else:
                    upgrade.append(item[0])

            info_msg.append(
                'Packages to be upgraded: ' + '; '.join(upgrade)
            )

        if downgrade0:
            downgrade = []
            for item in downgrade0:
                downgrade.append(' -> '.join(item))

            info_msg.append(
                'Packages to be downgraded: ' + '; '.join(downgrade)
            )

        if diff_ver0:
            diff_ver = []
            for item in diff_ver0:
                diff_ver.append(' -> '.join(item))

            info_msg.append(
                'Packages to be installed with different version: ' + '; '.join(
                    diff_ver
                )
            )

        if not_found:
            warn_msg.append(
                'Packages not found: ' + '; '.join(not_found)
            )

        return info_msg, warn_msg
