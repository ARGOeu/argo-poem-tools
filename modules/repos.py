import os
import shutil
import subprocess

import requests


class YUMRepos:
    def __init__(
            self, hostname, token, profiles, repos_path='/etc/yum.repos.d',
            override=True
    ):
        self.hostname = hostname
        self.token = token
        self.profiles = profiles
        self.path = repos_path
        self.override = override
        self.data = None
        self.missing_packages = None

    def get_data(self, include_internal=False):
        headers = {
            'x-api-key': self.token,
            'profiles': self._refine_list_of_profiles()
        }
        response = requests.get(self._build_url(), headers=headers, timeout=180)

        data_internal = None
        missing_packages_internal = list()
        if include_internal:
            response_internal = requests.get(
                self._build_url(include_internal=True),
                headers={"x-api-key": self.token},
                timeout=180
            )

            if response_internal.status_code == 200:
                internal_json = response_internal.json()
                data_internal = internal_json["data"]
                missing_packages_internal = internal_json["missing_packages"]

            else:
                try:
                    msg = response_internal.json()["detail"]

                except (ValueError, TypeError, KeyError):
                    msg = f"{response_internal.status_code} " \
                          f"{response_internal.reason}"

                raise requests.exceptions.RequestException(msg)

        if response.status_code == 200:
            data_json = response.json()
            self.data = data_json["data"]
            if data_internal:
                for name, info in data_internal.items():
                    if name in self.data:
                        p = self.data[name]["packages"] + info["packages"]
                        packages = dict((v["name"], v) for v in p).values()
                        self.data[name]["packages"] = sorted(
                            packages, key=lambda k: k["name"]
                        )

            self.missing_packages = sorted(
                list(set(
                    data_json['missing_packages'] + missing_packages_internal
                ))
            )

            return self.data

        else:
            try:
                msg = response.json()['detail']

            except (ValueError, TypeError, KeyError):
                msg = '%s %s' % (response.status_code, response.reason)

            raise requests.exceptions.RequestException(msg)

    def create_file(self):
        if not self.data:
            self.get_data()

        files = []
        for key, value in self.data.items():
            title = key
            filename = os.path.join(self.path, title + '.repo')
            content = value['content']

            files.append(filename)

            if not self.override:
                os.makedirs('/tmp' + self.path, exist_ok=True)
                if os.path.isfile(filename):
                    shutil.copyfile(filename, '/tmp' + filename)

            with open(filename, 'w') as f:
                f.write(content)

        return sorted(files)

    def clean(self):
        if not self.override:
            tmp_dir = '/tmp' + self.path
            if os.path.isdir(tmp_dir):
                src_files = os.listdir(tmp_dir)
                for file in src_files:
                    full_filename = os.path.join(tmp_dir, file)
                    if os.path.isfile(full_filename):
                        shutil.copy(full_filename, self.path)

                shutil.rmtree(tmp_dir)

        subprocess.call(['yum', 'clean', 'all'])

    @classmethod
    def _get_centos_version(cls):
        string = subprocess.check_output(['rpm', '-q', 'centos-release'])

        string = string.decode('utf-8')

        return 'centos' + string.split('-')[2]

    def _build_url(self, include_internal=False):
        hostname = self.hostname
        if hostname.startswith('https://'):
            hostname = hostname[8:]

        if hostname.startswith('http://'):
            hostname = hostname[7:]

        if hostname.endswith('/'):
            hostname = hostname[0:-1]

        if include_internal:
            repos = "repos_internal"

        else:
            repos = "repos"

        return f"https://{hostname}/api/v2/{repos}/{self._get_centos_version()}"

    def _refine_list_of_profiles(self):
        return '[' + ', '.join(self.profiles) + ']'
