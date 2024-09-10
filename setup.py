from setuptools import setup, find_packages

setup(
    name="bails-wallet",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "bip32"
    ],
)