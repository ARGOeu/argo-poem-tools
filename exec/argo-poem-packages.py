#!/usr/bin/python3
import argparse
import logging
import logging.handlers
import subprocess
import sys

import requests
from argo_poem_tools.config import Config
from argo_poem_tools.exceptions import ConfigException, PackageException, \
    POEMException, MergingException
from argo_poem_tools.packages import Packages
from argo_poem_tools.poem import POEM, merge_tenants_data
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
    parser.add_argument(
        "--include-internal", action="store_true", dest="include_internal",
        help="install probes for internal metrics as well as the ones in "
             "metric profiles"
    )
    args = parser.parse_args()
    noop = args.noop
    backup_repos = args.backup
    include_internal = args.include_internal

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
        tenants_configurations = config.get_configuration()

        tenant_repos = dict()
        for tenant, configuration in tenants_configurations.items():
            logger.info(
                f"{tenant}: Sending request for profile(s): "
                f"{', '.join(configuration['metricprofiles'])}"
            )

            poem = POEM(
                hostname=configuration["host"],
                token=configuration["token"],
                profiles=configuration["metricprofiles"]
            )

            tenant_repos.update({
                tenant: poem.get_data(include_internal=include_internal)
            })

        data = merge_tenants_data(tenant_repos)

        if backup_repos:
            repos = YUMRepos(data=data, override=False)

        else:
            repos = YUMRepos(data=data)

        logger.info("Creating YUM repo files...")

        files = repos.create_file(include_internal=include_internal)

        logger.info(f"Created files: {'; '.join(files)}")

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
                missing_packages_msg = (
                    f"Missing packages for given distro: "
                    f"{', '.join(repos.missing_packages)}"
                )
                logger.warning(missing_packages_msg)

            if not noop:
                if missing_packages_msg:
                    print(f"WARNING: {missing_packages_msg}")

            logger.info("The run finished successfully.")
            sys.exit(0)

    except (
            requests.exceptions.ConnectionError,
            requests.exceptions.RequestException,
            ConfigException,
            POEMException,
            MergingException,
            PackageException
    ) as err:
        logger.error(err)
        sys.exit(2)


if __name__ == '__main__':
    main()
