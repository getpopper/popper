import os

from setuptools import setup

version = {"__popper_version__": "0.0.0"}
version_file = "./popper/_version.py"
if os.path.isfile(version_file):
    with open(version_file) as f:
        exec(f.read(), version)

setup(
    name="popper",
    version=version["__popper_version__"],
    author="The Popper Development Team",
    author_email="ivotron@ucsc.edu",
    url="https://getpopper.io",
    description="Popper CLI tool to generate reproducible papers.",
    packages=["popper", "popper.commands"],
    include_package_data=True,
    install_requires=[
        "click==7.1.2",
        "docker==4.3.1",
        "dockerpty==0.4.1",
        "GitPython==3.1.7",
        "pykwalify==1.7.0",
        "python-box==5.1.1",
        "pyyaml==5.3.1",
        "spython==0.0.79",
        "kubernetes==11.0.0",
    ],
    extras_require={
        "dev": ["testfixtures==6.14.1", "black==19.10b0", "dunamai==1.3.0"]
    },
    entry_points="""
        [console_scripts]
        popper=popper.cli:cli
    """,
    project_urls={
        "Documentation": "https://popper.readthedocs.io",
        "Source": "https://github.com/getpopper/popper/",
        "Tracker": "https://github.com/getpopper/popper/issues",
    },
    keywords="popper reproducibility automation continuous-integration",
    license="MIT",
)
