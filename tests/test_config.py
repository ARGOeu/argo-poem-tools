import os
import unittest

from argo_poem_tools.config import Config, ConfigException

mock_file_name = 'mock-file.conf'


file_ok = """
[tenant1]
Host = tenant1.example.com
Token = some-token-1234
MetricProfiles = TEST_PROFILE1, TEST_PROFILE2

[tenant2]
Host = tenant2.example.com
Token = some-token-5678
MetricProfiles = TEST_PROFILE3, TEST_PROFILE4
"""

file_missing_host = """
[tenant1]
Token = some-token-1234
MetricProfiles = TEST_PROFILE1, TEST_PROFILE2

[tenant2]
Host = tenant2.example.com
Token = some-token-5678
MetricProfiles = TEST_PROFILE3, TEST_PROFILE4
"""

file_missing_token = """
[tenant1]
Host = tenant1.example.com
Token = some-token-1234
MetricProfiles = TEST_PROFILE1, TEST_PROFILE2

[tenant2]
Host = tenant2.example.com
MetricProfiles = TEST_PROFILE3, TEST_PROFILE4
"""

file_missing_profiles = """
[tenant1]
Host = tenant1.example.com
Token = some-token-1234

[tenant2]
Host = tenant2.example.com
Token = some-token-5678
MetricProfiles = TEST_PROFILE3, TEST_PROFILE4
"""


class ConfigTests(unittest.TestCase):
    def tearDown(self):
        if os.path.isfile(mock_file_name):
            os.remove(mock_file_name)

    def test_get_configuration(self):
        with open(mock_file_name, 'w') as f:
            f.write(file_ok)

        config = Config(file=mock_file_name)
        self.assertEqual(
            config.get_configuration(), {
                "tenant1": {
                    "host": "tenant1.example.com",
                    "token": "some-token-1234",
                    "metricprofiles": ["TEST_PROFILE1", "TEST_PROFILE2"]
                },
                "tenant2": {
                    "host": "tenant2.example.com",
                    "token": "some-token-5678",
                    "metricprofiles": ["TEST_PROFILE3", "TEST_PROFILE4"]
                }
            }
        )

    def test_get_configuration_no_host(self):
        with open(mock_file_name, 'w') as f:
            f.write(file_missing_host)

        config = Config(file=mock_file_name)
        with self.assertRaises(ConfigException) as context:
            config.get_configuration()

        self.assertEqual(
            context.exception.__str__(),
            "Configuration file error: Missing 'host' entry for tenant "
            "'tenant1'"
        )

    def test_get_configuration_token_missing(self):
        with open(mock_file_name, 'w') as f:
            f.write(file_missing_token)

        config = Config(file=mock_file_name)

        with self.assertRaises(ConfigException) as context:
            config.get_configuration()

        self.assertEqual(
            context.exception.__str__(),
            "Configuration file error: Missing 'token' entry for tenant "
            "'tenant2'"
        )

    def test_get_configuration_profiles_missing(self):
        with open(mock_file_name, 'w') as f:
            f.write(file_missing_profiles)

        config = Config(file=mock_file_name)

        with self.assertRaises(ConfigException) as context:
            config.get_configuration()

        self.assertEqual(
            context.exception.__str__(),
            "Configuration file error: Missing 'metricprofiles' entry for "
            "tenant 'tenant1'"
        )


if __name__ == '__main__':
    unittest.main()
