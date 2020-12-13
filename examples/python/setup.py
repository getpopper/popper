from setuptools import setup, find_packages

setup(
    name="MyPackage",
    version="0.0.1",
    url="https://github.com/myorg/mypackage.git",
    author="First Last",
    author_email="author@emails.com",
    description="What my package does",
    packages=["mypackage"],
    install_requires=["pytest >= 6.1.2", "black >= 20.8b1"],
)
