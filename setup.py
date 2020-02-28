from distutils.core import setup


NAME = 'argo-poem-tools'


def get_ver():
    try:
        for line in open(NAME + '.spec'):
            if "Version:" in line:
                return line.split()[1]

    except IOError:
        raise SystemExit(1)


setup(
    name=NAME,
    version=get_ver(),
    author='SRCE',
    author_email='kzailac@srce.hr',
    description='Script which installs packages on ARGO mon boxes.',
    url='https://github.com/ARGOeu/argo-poem-tools',
    package_dir={'argo_poem_tools': 'modules'},
    packages=['argo_poem_tools'],
    scripts=['exec/argo-poem-packages.py']
)
