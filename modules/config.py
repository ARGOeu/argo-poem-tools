import configparser

from argo_poem_tools.exceptions import ConfigException


class Config:
    def __init__(self, file="/etc/argo-poem-tools/argo-poem-tools.conf"):
        self.file = file
        self.conf = self._read()
        self.tenants = self._get_tenants()

    def _check_file_exists(self):
        conf = configparser.ConfigParser()
        try:
            with open(self.file) as f:
                conf.read_file(f)

        except IOError:
            raise ConfigException(f"File {self.file} does not exist")

    def _read(self):
        config = configparser.ConfigParser()
        config.read(self.file)
        return config

    def _get_tenants(self):
        tenants = list()
        for section in self.conf.sections():
            if section != "GENERAL":
                tenants.append(section)

        return tenants

    def get_configuration(self):
        configuration = dict()
        for tenant in self.tenants:
            for entry in ["host", "token", "metricprofiles"]:
                try:
                    if entry == "metricprofiles":
                        profiles_string = self.conf.get(tenant, entry)
                        value = [
                            p.strip() for p in profiles_string.split(',')
                        ]

                    else:
                        value = self.conf.get(tenant, entry)

                    if tenant in configuration:
                        configuration[tenant].update({entry: value})

                    else:
                        configuration.update({tenant: {entry: value}})

                except configparser.NoOptionError:
                    raise ConfigException(
                        f"Missing '{entry}' entry for tenant '{tenant}'"
                    )

        return configuration
