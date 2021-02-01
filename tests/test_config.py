import configparser
import os
import unittest

from argo_poem_tools.config import Config

mock_file_name = 'mock-file.conf'


file_ok = '[GENERAL]\nHost = egi.tenant.com\nToken = some-token-1234\n\n' \
          '[PROFILES]\nMetricProfiles = TEST_PROFILE1, TEST_PROFILE2'

file_missing_general = '[PROFILES]\nMetricProfiles = TEST_PROFILE1, ' \
                       'TEST_PROFILE2'

file_missing_host = '[GENERAL]\nToken = some-token-1234\n\n' \
                    '[PROFILES]\nMetricProfiles = TEST_PROFILE1, TEST_PROFILE2'

file_missing_token = '[GENERAL]\nHost = egi.tenant.com\n\n' \
                     '[PROFILES]\nMetricProfiles = TEST_PROFILE1, TEST_PROFILE2'

file_missing_profiles = '[GENERAL]\nHost = egi.tenant.com\n' \
                        'Token = some-token-1234'

file_missing_mp = '[GENERAL]\nHost = egi.tenant.com\nToken = some-token-1234' \
                  '\n\n[PROFILES]\nSomeProfiles = TEST_PROFILE1, TEST_PROFILE2'


class ConfigTests(unittest.TestCase):
    def tearDown(self):
        if os.path.isfile(mock_file_name):
            os.remove(mock_file_name)

    def test_read(self):
        with open(mock_file_name, 'w') as f:
            f.write(file_ok)

        config = Config()
        config.conf = mock_file_name

        self.assertTrue(config.read())

    def test_get_hostname(self):
        with open(mock_file_name, 'w') as f:
            f.write(file_ok)

        config = Config()
        config.conf = mock_file_name
        self.assertEqual(config.get_hostname(), 'egi.tenant.com')

    def test_get_hostname_no_section(self):
        with open(mock_file_name, 'w') as f:
            f.write(file_missing_general)

        config = Config()
        config.conf = mock_file_name
        self.assertRaises(
            configparser.NoSectionError,
            config.get_hostname
        )

    def test_get_hostname_no_option(self):
        with open(mock_file_name, 'w') as f:
            f.write(file_missing_host)

        config = Config()
        config.conf = mock_file_name

        self.assertRaises(
            configparser.NoOptionError,
            config.get_hostname
        )

    def test_get_token(self):
        with open(mock_file_name, 'w') as f:
            f.write(file_ok)

        config = Config()
        config.conf = mock_file_name
        self.assertEqual(config.get_token(), 'some-token-1234')

    def test_get_token_no_section(self):
        with open(mock_file_name, 'w') as f:
            f.write(file_missing_general)

        config = Config()
        config.conf = mock_file_name

        self.assertRaises(
            configparser.NoSectionError,
            config.get_token
        )

    def test_get_token_no_option(self):
        with open(mock_file_name, 'w') as f:
            f.write(file_missing_token)

        config = Config()
        config.conf = mock_file_name

        self.assertRaises(
            configparser.NoOptionError,
            config.get_token
        )

    def test_get_profiles(self):
        with open(mock_file_name, 'w') as f:
            f.write(file_ok)

        config = Config()
        config.conf = mock_file_name

        self.assertEqual(
            config.get_profiles(), ['TEST_PROFILE1', 'TEST_PROFILE2']
        )

    def test_get_profiles_no_section(self):
        with open(mock_file_name, 'w') as f:
            f.write(file_missing_profiles)

        config = Config()
        config.conf = mock_file_name
        self.assertRaises(
            configparser.NoSectionError,
            config.get_profiles
        )

    def test_get_profiles_no_option(self):
        with open(mock_file_name, 'w') as f:
            f.write(file_missing_mp)

        config = Config()
        config.conf = mock_file_name
        self.assertRaises(
            configparser.NoOptionError,
            config.get_profiles
        )


if __name__ == '__main__':
    unittest.main()
