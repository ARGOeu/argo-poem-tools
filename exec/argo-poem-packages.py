#!/usr/bin/python3
import argparse
import configparser
import logging
import logging.handlers
import subprocess
import sys

import requests
from argo_poem_tools.config import Config
from argo_poem_tools.packages import Packages, PackageException
from argo_poem_tools.repos import YUMRepos

LOGFILE = "/var/log/argo-poem-tools/argo-poem-tools.log"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--noop', action='store_true', dest='noop',
        help='run script without installing'
    )
    parser.add_argument(
        '--backup-repos', action='store_true', dest='backup',
        help='backup/restore yum repos instead overriding them'
    )
    args = parser.parse_args()
    noop = args.noop
    backup_repos = args.backup

    logger = logging.getLogger("argo-poem-packages")
    logger.setLevel(logging.INFO)

    stdout = logging.StreamHandler()
    if not noop:
        stdout.setLevel(logging.WARNING)

    stdout.setFormatter(
        logging.Formatter("%(levelname)s - %(message)s")
    )
    logger.addHandler(stdout)

    # setting up logging to file
    logfile = logging.handlers.RotatingFileHandler(
        LOGFILE, maxBytes=512 * 1024, backupCount=5
    )
    logfile.setLevel(logging.INFO)
    logfile.setFormatter(logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        "%Y-%m-%d %H:%M:%S"
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
        if backup_repos:
            repos = YUMRepos(
                hostname=hostname, token=token, profiles=profiles,
                override=False
            )

        else:
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

            files = repos.create_file()

            logger.info('Created files: ' + '; '.join(files))

            pkg = Packages(data)

            if noop:
                info_msg, warn_msg = pkg.no_op()

            else:
                info_msg, warn_msg = pkg.install()

            # if there were repo files backed up, now they are restored
            repos.clean()

            if info_msg:
                for msg in info_msg:
                    logger.info(msg)

            if warn_msg:
                for msg in warn_msg:
                    logger.warning(msg)

                sys.exit(1)

            else:
                missing_packages_msg = ''
                if repos.missing_packages:
                    missing_packages_msg = \
                        'Missing packages for given distro: ' + \
                        ', '.join(repos.missing_packages)
                    logger.warning(missing_packages_msg)

                if not noop:
                    if missing_packages_msg:
                        print('WARNING: ' + missing_packages_msg)

                logger.info("The run finished successfully.")
                sys.exit(0)

    except requests.exceptions.ConnectionError as err:
        logger.error(err)
        sys.exit(2)

    except requests.exceptions.RequestException as err:
        logger.error(err)
        sys.exit(2)

    except configparser.ParsingError as err:
        logger.error(err)
        sys.exit(2)

    except configparser.NoSectionError as err:
        logger.error(err)
        sys.exit(2)

    except configparser.NoOptionError as err:
        logger.error(err)
        sys.exit(2)

    except PackageException as err:
        logger.error(err)
        sys.exit(2)


if __name__ == '__main__':
    main()
