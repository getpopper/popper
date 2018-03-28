from setuptools import setup
import popper

version = {}
with open('popper/__init__.py') as f:
    exec(f.read(), version)

setup(
    name='popper',
    version=version['__version__'],
    author='The Popper Development Team',
    author_email='ivo@cs.ucsc.edu',
    url='http://falsifiable.us',
    description='Popper CLI tool to generate reproducible papers.',
    data_files=[
        ('/etc/bash_completion.d', ['./extras/bash-completion.sh']),
        ],
    packages=['popper', 'popper.commands'],
    include_package_data=True,
    install_requires=[
        'click',
        'requests',
        'ruamel.yaml<0.15'
    ],
    entry_points='''
        [console_scripts]
        popper=popper.cli:cli
    ''',
    project_urls={
        'Documentation': 'https://popper.readthedocs.io',
        'Say Thanks!': 'http://gitter.im/falsifiable-us/popper',
        'Source': 'https://github.com/systemslab/popper/',
        'Tracker': 'https://github.com/systemslab/popper/',
    },
    keywords='popper reproducibility automation continuous-integration',
    license='MIT',
)
