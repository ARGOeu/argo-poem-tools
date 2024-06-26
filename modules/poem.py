import subprocess

import requests
from argo_poem_tools.exceptions import POEMException, MergingException


def merge_tenants_data(data):
    merged_data = dict()

    for tenant, repos in data.items():
        for name, info in repos.items():
            if name not in merged_data:
                merged_data.update({name: info})

            else:
                if name == "missing_packages":
                    incoming_missing = set(repos[name])
                    existing_missing = set(merged_data[name])
                    merged_data["missing_packages"] = sorted(
                        list(incoming_missing.union(existing_missing))
                    )

                else:
                    existing_packages = merged_data[name]["packages"]
                    existing_names = [
                        item["name"] for item in existing_packages
                    ]

                    for package in info["packages"]:
                        if package["name"] not in existing_names:
                            existing_packages.append(package)

                        if (
                                package["name"] in existing_names and
                                package not in existing_packages
                        ):
                            raise MergingException(
                                f"Package '{package['name']}' must be the same "
                                f"version across all tenants"
                            )

                    merged_data[name]["packages"] = sorted(
                        existing_packages, key=lambda p: p["name"]
                    )

    return merged_data


class POEM:
    def __init__(self, hostname, token, profiles):
        self.hostname = hostname
        self.token = token
        self.profiles = profiles
        self.missing_packages = None

    @staticmethod
    def _get_os():
        string = subprocess.check_output(["cat", "/etc/os-release"])

        string = string.decode('utf-8')

        string_list = string.split("\n")

        name = [
            line.split("=")[1].lower().split(" ")[0].replace('"', "") for line
            in string_list if line.startswith("NAME")
        ][0]

        version = [
            line.split("=")[1].split(".")[0].replace('"', "") for
            line in string_list if line.startswith("VERSION_ID")
        ][0]

        return f"{name}{version}"

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

        return f"https://{hostname}/api/v2/{repos}/{self._get_os()}"

    def _refine_list_of_profiles(self):
        return f"[{', '.join(self.profiles)}]"

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
                msg = f"{response_internal.status_code} " \
                      f"{response_internal.reason}"

                try:
                    msg = f"{msg}: {response_internal.json()['detail']}"

                except (ValueError, TypeError, KeyError):
                    pass

                raise POEMException(msg)

        if response.status_code == 200:
            data_json = response.json()
            data = data_json["data"]
            if data_internal:
                for name, info in data_internal.items():
                    if name in data:
                        p = data[name]["packages"] + info["packages"]
                        packages = dict((v["name"], v) for v in p).values()
                        data[name]["packages"] = sorted(
                            packages, key=lambda k: k["name"]
                        )

            self.missing_packages = sorted(
                list(set(
                    data_json['missing_packages'] + missing_packages_internal
                ))
            )

            return data

        else:
            msg = f"{response.status_code} {response.reason}"

            try:
                msg = f"{msg}: {response.json()['detail']}"

            except (ValueError, TypeError, KeyError):
                pass

            raise POEMException(msg)
