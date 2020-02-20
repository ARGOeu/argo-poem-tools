#!/usr/bin/python
import subprocess
import rpm
import yum


class Packages:
    def __init__(self, data):
        self.data = data
        self.yb = yum.YumBase()

    def list_of_packages(self):
        list_packages = []
        for key, value in self.data[0].items():
            for item in value['packages']:
                list_packages.append((item['name'], item['version']))

        return list_packages

    def get_packages(self):
        pkgs = self.yb.rpmdb.returnPackages()
        installed = [(pkg.name, pkg.version) for pkg in pkgs]

        install = []
        downgrade = []
        for item in self.list_of_packages():
            if item[0] in [x[0] for x in installed]:
                installed_ver = installed[
                    [x[0] for x in installed].index(item[0])
                ][1]

                if item not in self.exact_packages_not_found():
                    if rpm.labelCompare(
                            ('mock', item[1], 'mock'),
                            ('mock', installed_ver, 'mock')
                    ) >= 0:
                        install.append(item[0] + '-' + item[1])
                    elif rpm.labelCompare(
                            ('mock', item[1], 'mock'),
                            ('mock', installed_ver, 'mock')
                    ) < 0:
                        downgrade.append(item[0] + '-' + item[1])

            else:
                if item not in self.exact_packages_not_found():
                    install.append(item[0] + '-' + item[1])

                else:
                    if item[0] in [
                        p[0] for p in
                        self.packages_found_with_different_version()
                    ]:
                        install.append(item[0])

        return install, downgrade

    def exact_packages_not_found(self):
        pkgs = self.yb.pkgSack.returnPackages()
        avail = [(pkg.name, pkg.version) for pkg in pkgs]

        pkg_not_found = []
        for item in self.list_of_packages():
            if item not in avail:
                pkg_not_found.append(item)

        return pkg_not_found

    def packages_found_with_different_version(self):
        pkgs = self.yb.pkgSack.returnPackages()
        avail = [(pkg.name, pkg.version) for pkg in pkgs]

        pkg_wrong_version = []
        for item in self.list_of_packages():
            if item in self.exact_packages_not_found() and \
                    item[0] in [a[0] for a in avail]:
                pkg_wrong_version.append(
                    avail[[a[0] for a in avail].index(item[0])]
                )

        return pkg_wrong_version

    def packages_not_found(self):
        pkgs_not_found = []
        for pkg in self.exact_packages_not_found():
            if pkg[0] not in [
                p[0] for p in self.packages_found_with_different_version()
            ]:
                pkgs_not_found.append(pkg)

        return pkgs_not_found

    def get_packages_not_found(self):
        pkgs_not_found = []
        for pkg in self.packages_not_found():
            pkgs_not_found.append('%s-%s' % (pkg[0], pkg[1]))

        return pkgs_not_found

    def get_packages_installed_with_different_version(self):
        pkgs = []
        for item in self.packages_found_with_different_version():
            orig_item = self.list_of_packages()[
                [p[0] for p in self.list_of_packages()].index(item[0])
            ]
            pkgs.append(
                '%s-%s -> %s-%s' % (
                    orig_item[0], orig_item[1], item[0], item[1]
                )
            )

        return pkgs

    def get_packages_installed_with_versions_as_requested(self, installed):
        new_installed = []
        for item in installed:
            if item not in [
                p[0] for p in self.packages_found_with_different_version()
            ]:
                new_installed.append(item)

        return new_installed

    def install_packages(self):
        install, downgrade = self.get_packages()
        installed = []
        not_installed = []
        downgraded = []
        not_downgraded = []
        if install:
            for pkg in install:
                try:
                    subprocess.check_call(['yum', '-y', 'install', pkg])
                    installed.append(pkg)

                except subprocess.CalledProcessError:
                    not_installed.append(pkg)

        if downgrade:
            for pkg in downgrade:
                try:
                    subprocess.check_call(['yum', '-y', 'downgrade', pkg])
                    downgraded.append(pkg)

                except subprocess.CalledProcessError:
                    not_downgraded.append(pkg)

        return installed, not_installed, downgraded, not_downgraded
