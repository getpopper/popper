from setuptools import setup

setup(
    name='popper',
    version='0.6-dev',
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
)
