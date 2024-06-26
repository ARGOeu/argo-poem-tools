import subprocess
from re import compile

from argo_poem_tools.exceptions import PackageException

_rpm_re = compile('(\S+)-(?:(\d*):)?(.*)-(~?\w+[\w.]*)')


def _pop_arch(pkg_string):
    """
    Pop arch info from RPM package string.
    :param pkg_string: string with arch info
    :return: RPM package string without arch info
    """
    pkg_string_split = pkg_string.split('.')
    pkg = '.'.join(pkg_string_split[:-1])
    return pkg


def _compare_versions(v1, v2):
    """
    Compares two RPM version strings.
    :param v1: first string version
    :param v2: second string version
    :return: 1 if v1 is newer, 0 if they are equal, -1 if v2 is newer
    """
    arr1 = v1.split('.')
    arr2 = v2.split('.')

    arr1 = [int(i) if i.isnumeric() else i for i in arr1]
    arr2 = [int(i) if i.isnumeric() else i for i in arr2]

    n = len(arr1)
    m = len(arr2)

    if n > m:
        for i in range(m, n):
            arr2.append(0)
    elif m > n:
        for i in range(n, m):
            arr1.append(0)

    for i in range(len(arr1)):
        if arr1[i] > arr2[i]:
            return 1
        elif arr2[i] > arr1[i]:
            return -1

    return 0


def _compare_vr(vr1, vr2):
    """
    Compares two RPM (version, release) tuples.
    :param vr1: first (version, release) tuple
    :param vr2: second (version, release) tuple
    :return: 1 if vr1 is newer, 0 if equal, -1 if vr2 is newer
    """
    v1, r1 = vr1
    v2, r2 = vr2

    if v1 == v2:
        if r1 == r2:
            return 0

        else:
            return _compare_versions(r1, r2)

    else:
        return _compare_versions(v1, v2)


class Packages:
    def __init__(self, data):
        self.data = data
        self.package_list = self._list()
        self.versions_unlocked = False
        self.initially_locked_versions = []
        self.locked_versions = []
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

    def _get_locked_versions(self):
        """
        Get list of packages with locked versions among the packages requested.
        """
        output = subprocess.check_output(['yum', 'versionlock', 'list']).decode(
            'utf-8'
        )
        locked_versions = [
            item[0] for item in self._list() if item[0] in output
        ]
        self.locked_versions = locked_versions

    def _failsafe_lock_versions(self):
        """
        Locking the packages that have already been locked in case of exception.
        """
        warn = []
        for item in self.initially_locked_versions:
            try:
                subprocess.call(
                    ['yum', 'versionlock', 'add', item],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )

            except subprocess.CalledProcessError:
                warn.append(item)

        if warn:
            return 'Packages not locked: {}'.format(', '.join(warn))

        else:
            return None

    def _unlock_versions(self):
        if len(self.locked_versions) == 0:
            self._get_locked_versions()

        if len(self.locked_versions) > 0:
            for item in self.locked_versions:
                try:
                    subprocess.call(
                        ['yum', 'versionlock', 'delete', item],
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE
                    )
                    self.initially_locked_versions.append(item)

                except subprocess.CalledProcessError:
                    continue

            self.versions_unlocked = True

    def _get_available_packages(self):
        if not self.versions_unlocked:
            self._unlock_versions()

        output = subprocess.check_output(
            ['yum', 'list', 'available', '--showduplicates']
        )
        output_list = output.decode('utf-8').split('\n')
        pkg_index = output_list.index('Available Packages') + 1
        pkgs = output_list[pkg_index:]
        pkgs = ' '.join(pkgs)
        pkg_list = list(filter(None, pkgs.split(' ')))

        formatted_pkgs = []
        for i in range(0, len(pkg_list), 3):
            formatted_pkgs.append(pkg_list[i:i + 3])

        pkgs_dicts = []
        for pkg in formatted_pkgs:
            pkg_list_split = pkg[1].split('-')
            version = pkg_list_split[0]
            release = pkg_list_split[1]
            pkgs_dicts.append(
                dict(
                    name=_pop_arch(pkg[0]),
                    version=version,
                    release=release
                )
            )

        return pkgs_dicts

    def _get_exceptions(self):
        """
        Go through packages available from YUM repo, and determine which one of
        them are found with different version and which one are not found at
        all.
        """
        pkgs = self._get_available_packages()
        self.available_packages = [
            (pkg['name'], pkg['version'], pkg['release']) for pkg in pkgs
        ]
        available_vr = [(pkg['name'], pkg['version']) for pkg in pkgs]

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
                        if _compare_vr(
                                (version[1], 'mock'),
                                (max_version[1], 'mock')
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
    def _get_installed_packages():
        output = subprocess.check_output(['rpm', '-qa'])
        output_list = output.decode('utf-8').split('\n')
        pkg_list = []
        for item in output_list:
            if item:
                try:
                    n, e, v, r = _rpm_re.match(_pop_arch(item.strip())).groups()
                    pkg_list.append(dict(name=n, version=v, release=r))

                except AttributeError:
                    continue

        return pkg_list

    @staticmethod
    def _get_max_version(available_packages):
        max_version = available_packages[0]
        for version in available_packages:
            if _compare_vr(
                    (version[1], version[2]),
                    (max_version[1], max_version[2])
            ) > 0:
                max_version = version

        return max_version

    def _get(self):
        if not self.packages_different_version:
            self._get_exceptions()

        pkgs = self._get_installed_packages()
        installed_packages = [
            (pkg['name'], pkg['version'], pkg['release']) for pkg in pkgs
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

                max_version = self._get_max_version(available_items)

                if len(item) > 1:
                    if item[1] == installed_ver:
                        change_tuple = (item,)
                    else:
                        change_tuple = (
                            (item[0], installed_ver), item
                        )

                else:
                    change_tuple = (item,)

                if _compare_vr(
                        (max_version[1], max_version[2]),
                        (installed_ver, installed_release)
                ) > 0:
                    upgrade.append(change_tuple)

                elif _compare_vr(
                        (max_version[1], max_version[2]),
                        (installed_ver, installed_release)
                ) < 0:
                    downgrade.append(change_tuple)

                else:
                    continue

            else:
                install.append(item)

        diff_ver = []
        for item in self.packages_different_version:
            orig_item = self.package_list[
                [p[0] for p in self.package_list].index(item[0])
            ]
            diff_ver.append('-'.join(orig_item))

        not_found = []
        for item in self.packages_not_found:
            if len(item) > 1:
                not_found.append('-'.join(item))
            else:
                not_found.append(item[0])

        return install, upgrade, downgrade, diff_ver, not_found

    def install(self):
        try:
            install, upgrade, downgrade, diff_ver, not_found = self._get()
            installed = []
            not_installed = []
            upgraded = []
            not_upgraded = []
            downgraded = []
            not_downgraded = []
            not_locked = []
            if install:
                for pkg in install:
                    if len(pkg) == 2:
                        pkgi = '-'.join(pkg)
                    else:
                        pkgi = pkg[0]

                    try:
                        subprocess.check_call(['yum', '-y', 'install', pkgi])
                        installed.append(pkgi)

                    except subprocess.CalledProcessError:
                        not_installed.append(pkgi)

            if upgrade:
                for pkg in upgrade:
                    try:
                        if len(pkg) == 2:
                            subprocess.check_call(
                                ['yum', '-y', 'install', '-'.join(pkg[1])]
                            )
                            upgraded.append(
                                '{} -> {}'.format(
                                    '-'.join(pkg[0]), '-'.join(pkg[1])
                                )
                            )

                        else:
                            subprocess.check_call(
                                ['yum', '-y', 'install', '-'.join(pkg[0])]
                            )
                            upgraded.append('-'.join(pkg[0]))

                    except subprocess.CalledProcessError:
                        not_upgraded.append('-'.join(pkg[0]))

            if downgrade:
                for pkg in downgrade:
                    try:
                        subprocess.check_call(
                            ['yum', '-y', 'downgrade', '-'.join(pkg[1])]
                        )
                        downgraded.append(
                            '{} -> {}'.format(
                                '-'.join(pkg[0]), '-'.join(pkg[1])
                            )
                        )

                    except subprocess.CalledProcessError:
                        not_downgraded.append('-'.join(pkg[0]))

            lock_msg = self._lock_versions()

            info_msg = []
            warn_msg = []
            if installed:
                info_msg.append('Packages installed: ' + '; '.join(installed))

            if upgraded:
                info_msg.append('Packages upgraded: ' + '; '.join(upgraded))

            if downgraded:
                info_msg.append('Packages downgraded: ' + '; '.join(downgraded))

            if diff_ver:
                warn_msg.append(
                    'Packages not found with requested version: ' + '; '.join(
                        diff_ver
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

            if not_locked:
                warn_msg.append(
                    'Packages not locked: ' + '; '.join(not_locked)
                )

            if not_found:
                warn_msg.append(
                    'Packages not found: ' + '; '.join(not_found)
                )

            if lock_msg:
                warn_msg.append(lock_msg)

            return info_msg, warn_msg

        except Exception as e:
            self._failsafe_lock_versions()
            raise PackageException(f"Error installing packages: {str(e)}")

    def no_op(self):
        try:
            install, upgrade0, downgrade0, diff_ver, not_found = self._get()

            self._lock_versions()

            info_msg = []
            warn_msg = []

            if install:
                info_msg.append(
                    'Packages to be installed: ' + '; '.join(
                        ['-'.join(item) for item in install]
                    )
                )

            if upgrade0:
                upgrade = []
                for item in upgrade0:
                    if len(item) > 1:
                        upgrade.append(
                            '{} -> {}'.format(
                                '-'.join(item[0]), '-'.join(item[1])
                            )
                        )
                    else:
                        upgrade.append('-'.join(item[0]))

                info_msg.append(
                    'Packages to be upgraded: ' + '; '.join(upgrade)
                )

            if downgrade0:
                downgrade = []
                for item in downgrade0:
                    downgrade.append(
                        '{} -> {}'.format(
                            '-'.join(item[0]), '-'.join(item[1])
                        )
                    )

                info_msg.append(
                    'Packages to be downgraded: ' + '; '.join(downgrade)
                )

            if diff_ver:
                warn_msg.append(
                    'Packages not found with requested version: ' + '; '.join(
                        diff_ver
                    )
                )

            if not_found:
                warn_msg.append(
                    'Packages not found: ' + '; '.join(not_found)
                )

            return info_msg, warn_msg

        except Exception as e:
            self._failsafe_lock_versions()
            raise PackageException(f"Error analysing packages: {str(e)}")

    def _lock_versions(self):
        self._get_locked_versions()

        installed_pkgs = self._get_installed_packages()
        installed_names = [pkg['name'] for pkg in installed_pkgs]

        warn = []
        for item in self._list():
            if len(item) > 1 and item[0] in installed_names and \
                    not item[0] in self.locked_versions:
                try:
                    subprocess.call(
                        ['yum', 'versionlock', 'add', item[0]],
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE
                    )

                except subprocess.CalledProcessError:
                    warn.append(item[0])

        if warn:
            return 'Packages not locked: {}'.format(', '.join(warn))

        else:
            return None
