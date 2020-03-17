#!/usr/bin/python
import ConfigParser
import logging
import subprocess
import sys

import requests
from argo_poem_tools.config import Config
from argo_poem_tools.packages import Packages
from argo_poem_tools.repos import build_api_url, create_yum_repo_file, \
    get_repo_data


def main():
    logger = logging.getLogger('argo-poem-packages')
    logger.setLevel(logging.INFO)

    # setting up logging to file
    logfile = logging.FileHandler('/var/log/messages')
    logfile.setLevel(logging.INFO)
    logfile.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))

    # add the handler to the root logger
    logger.addHandler(logfile)

    try:
        subprocess.call(['yum', 'clean', 'all'])

        config = Config()
        token = config.get_token()
        hostname = config.get_hostname()
        profiles = config.get_profiles()

        logger.info(
            'Sending request for profile(s): ' + ', '.join(profiles)
        )
        data = get_repo_data(
            build_api_url(hostname),
            token,
            profiles
        )

        if not data:
            logger.warning(
                'No data for given metric profile(s): ' +
                ', '.join(profiles)
            )
            sys.exit(2)

        else:
            logger.info('Creating YUM repo files...')
            create_yum_repo_file(data)

            pkg = Packages(data)

            installed, not_installed, downgraded, not_downgraded = \
                pkg.install_packages()

            warn_msg = []
            info_msg = []
            if pkg.get_packages_not_found():
                warn_msg.append(
                    'Packages not found: ' +
                    ', '.join(pkg.get_packages_not_found())
                )

            if installed:
                new_installed = \
                    pkg.get_packages_installed_with_versions_as_requested(
                        installed
                    )

                if new_installed:
                    info_msg.append(
                        'Packages installed: ' + ', '.join(new_installed)
                    )

                installed_diff = \
                    pkg.get_packages_installed_with_different_version()

                if installed_diff:
                    info_msg.append(
                        'Packages installed with different version: ' +
                        ', '.join(installed_diff)
                    )

            if not_installed:
                warn_msg.append(
                    'Packages not installed: ' + ', '.join(not_installed)
                )

            if downgraded:
                info_msg.append(
                    'Packages downgraded: ' + ', '.join(downgraded)
                )

            if not_downgraded:
                warn_msg.append(
                    'Packages not downgraded: ' + ', '.join(not_downgraded)
                )

            if info_msg:
                logger.info('; '.join(info_msg))

            if warn_msg:
                logger.warning('; '.join(warn_msg))
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
