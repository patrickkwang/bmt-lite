"""Set up PyPI package."""
from setuptools import setup, find_packages

version = "0.1.0"

description = (
    "Biolink Model Toolkit *Lite* - "
    "a collection of python functions for using the biolink model "
    "(https://github.com/biolink/biolink-model)"
)

requires = [
    "pyyaml>=5.1",
    "requests>=2.13.0"
]

setup(
    name="bmt-lite",
    version=version,
    packages=find_packages(),
    include_package_data=True,
    url="https://github.com/lhannest/biolink-model-toolkit",
    install_requires=requires,
    python_requires=">=3.6",
    description=description
)
