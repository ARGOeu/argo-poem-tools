import ConfigParser

conf = '/etc/argo-poem-tools/argo-poem-tools.conf'


class Config:
    def __init__(self):
        self.conf = conf

    def read(self):
        config = ConfigParser.ConfigParser()
        config.read(self.conf)
        return config

    def get_hostname(self):
        config = self.read()
        return config.get('GENERAL', 'host')

    def get_token(self):
        config = self.read()
        return config.get('GENERAL', 'token')

    def get_profiles(self):
        config = self.read()
        profiles_string = config.get('PROFILES', 'metricprofiles')
        profiles = [p.strip() for p in profiles_string.split(',')]

        return profiles
