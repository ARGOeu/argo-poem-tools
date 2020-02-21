#!/usr/bin/python
import argparse
import logging

from argo_poem_tools.packages import Packages
from argo_poem_tools.repos import build_api_url, create_yum_repo_file, \
    get_repo_data

import requests
import subprocess
import sys


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

    parser = argparse.ArgumentParser(
        description='Install packages for given metric profiles'
    )
    parser.add_argument(
        '-t', '--token', dest='token', type=str, help='POEM token'
    )
    parser.add_argument(
        '-p', '--profiles', dest='profile', type=str, nargs='*',
        help='space separated list of metric profiles'
    )
    parser.add_argument(
        '-H', '--hostname', dest='hostname', type=str, help='hostname'
    )
    args = parser.parse_args()

    error_args = list()
    if not args.token:
        error_args.append('token')

    if not args.profile:
        error_args.append('profile')

    if not args.hostname:
        error_args.append('hostname')

    if error_args:
        error_msg = ' and '.join(
            [', '.join(error_args[:-1]), error_args[-1]]
            if len(error_args) > 2 else error_args
        ).capitalize() + ' not given!'
        logger.error(error_msg)
        parser.error(error_msg)
        sys.exit(2)

    subprocess.call(['yum', 'clean', 'all'])

    try:
        logger.info(
            'Sending request for profile(s): ' + ', '.join(args.profile)
        )
        data = get_repo_data(
            build_api_url(args.hostname),
            args.token,
            args.profile
        )

        if not data:
            logger.warning(
                'No data for given metric profile(s): ' +
                ', '.join(args.profile)
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


if __name__ == '__main__':
    main()
