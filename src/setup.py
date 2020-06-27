from setuptools import setup

version = {}
with open("popper/_version.py") as f:
    exec(f.read(), version)

setup(
    name="popper",
    version=version["__popper_version__"],
    author="The Popper Development Team",
    author_email="ivo@cs.ucsc.edu",
    url="http://falsifiable.us",
    description="Popper CLI tool to generate reproducible papers.",
    packages=["popper", "popper.commands"],
    include_package_data=True,
    install_requires=[
        "click==7.1.2",
        "docker==4.2.0",
        "dockerpty==0.4.1",
        "GitPython==3.1.0",
        "pykwalify==1.7.0",
        "python-box==4.2.3",
        "pyyaml==5.3.1",
        "spython==0.0.79",
    ],
    extras_require={
        "dev": ["testfixtures==6.14.0", "black==19.10b0", "dunamai==1.1.0"]
    },
    entry_points="""
        [console_scripts]
        popper=popper.cli:cli
    """,
    project_urls={
        "Documentation": "https://popper.readthedocs.io",
        "Say Thanks!": "http://gitter.im/falsifiable-us/popper",
        "Source": "https://github.com/systemslab/popper/",
        "Tracker": "https://github.com/systemslab/popper/",
    },
    keywords="popper reproducibility automation continuous-integration",
    license="MIT",
)
