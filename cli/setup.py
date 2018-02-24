from setuptools import setup

setup(
    name='popper',
    version='0.6-dev0',
    author='The Popper Development Team',
    author_email='ivo@cs.ucsc.edu',
    url='http://falsifiable.us',
    description='Popper CLI tool to generate reproducible papers.',
    packages=['popper', 'popper.commands'],
    include_package_data=True,
    install_requires=[
        'click',
        'pyyaml'
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
