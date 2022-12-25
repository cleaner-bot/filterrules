import re
from pathlib import Path

from setuptools import find_namespace_packages, setup  # type: ignore

about = (Path("filterrules") / "__about__.py").read_text()
version = re.search(r"__version__ = [\"']([\d.]+)[\"']", about)
assert version

setup(
    name="filterrules",
    version=version.group(1),
    url="https://github.com/cleaner-bot/filterrules",
    author="Leo Developer",
    author_email="git@leodev.xyz",
    description="filter rules language",
    packages=find_namespace_packages(include=["filterrules*"]),
    package_data={"filterrules": ["py.typed"]},
)
