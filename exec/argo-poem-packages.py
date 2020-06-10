#!/usr/bin/python
import ConfigParser
import logging
import subprocess
import sys

import requests
from argo_poem_tools.config import Config
from argo_poem_tools.packages import Packages
from argo_poem_tools.repos import YUMRepos


def main():
    logger = logging.getLogger('argo-poem-packages')
    logger.setLevel(logging.INFO)

    stdout = logging.StreamHandler()

    # setting up logging to file
    logfile = logging.FileHandler('/var/log/messages')
    logfile.setLevel(logging.INFO)
    logfile.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))

    # add the handler to the root logger
    logger.addHandler(logfile)
    logger.addHandler(stdout)

    try:
        subprocess.call(['yum', 'clean', 'all'])

        config = Config()
        token = config.get_token()
        hostname = config.get_hostname()
        profiles = config.get_profiles()

        logger.info(
            'Sending request for profile(s): ' + ', '.join(profiles)
        )
        repos = YUMRepos(hostname=hostname, token=token, profiles=profiles)
        data = repos.get_data()

        if not data:
            logger.warning(
                'No data for given metric profile(s): ' +
                ', '.join(profiles)
            )
            sys.exit(2)

        else:
            logger.info('Creating YUM repo files...')
            repos.create_file()

            pkg = Packages(data)

            info_msg, warn_msg = pkg.install()

            if info_msg:
                for msg in info_msg:
                    logger.info(msg)

            if warn_msg:
                for msg in warn_msg:
                    logger.warning(msg)

                sys.exit(1)

            else:
                logger.info('ok!')
                sys.exit(0)

    except requests.exceptions.ConnectionError as err:
        logger.error(err)
        sys.exit(2)

    except requests.exceptions.RequestException as err:
        logger.error(err)
        sys.exit(2)

    except ConfigParser.ParsingError as err:
        logger.error(err)
        sys.exit(2)

    except ConfigParser.NoSectionError as err:
        logger.error(err)
        sys.exit(2)

    except ConfigParser.NoOptionError as err:
        logger.error(err)
        sys.exit(2)


if __name__ == '__main__':
    main()
