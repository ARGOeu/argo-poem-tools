import configparser


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

    def _get_entries(self, entry):
        data = dict()
        for tenant in self.tenants:
            try:
                if entry == "metricprofiles":
                    profiles_string = self.conf.get(tenant, entry)
                    profiles = [p.strip() for p in profiles_string.split(',')]

                    data.update({tenant: profiles})

                else:
                    data.update({tenant: self.conf.get(tenant, entry)})

            except configparser.NoOptionError:
                raise ConfigException(
                    f"Missing '{entry}' entry for tenant '{tenant}'"
                )

        return data

    def get_hostnames(self):
        return self._get_entries(entry="host")

    def get_tokens(self):
        return self._get_entries(entry="token")

    def get_profiles(self):
        return self._get_entries(entry="metricprofiles")


class ConfigException(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return f"Configuration file error: {str(self.msg)}"
