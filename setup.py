from distutils.core import setup

setup(
    name='argo-poem-tools',
    version='0.1.0',
    author='SRCE',
    author_email='kzailac@srce.hr',
    description='Script which installs packages on ARGO mon boxes.',
    package_dir={'argo_poem_tools': 'modules'},
    packages=['argo_poem_tools'],
    scripts=['exec/install_packages.py']
)
