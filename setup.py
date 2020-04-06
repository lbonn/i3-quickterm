import codecs
from os import path
import re

from setuptools import setup, find_packages

# from https://packaging.python.org/guides/single-sourcing-package-version/
here = path.abspath(path.dirname(__file__))


def read(*parts):
    with codecs.open(path.join(here, *parts), "r") as fp:
        return fp.read()


def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


with open(path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()


setup(
    name="i3-quickterm",
    version=find_version("i3_quickterm", "main.py"),
    description="A small drop-down terminal for i3 and sway",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/lbonn/i3-quickterm",
    author="lbonn",
    author_email="bonnans.l@gmail.com",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Desktop Environment",
        "Topic :: Terminals :: Terminal Emulators/X Terminals",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    keywords="i3 i3wm extensions add-ons",
    packages=find_packages(where="."),
    python_requires=">=3.4",
    install_requires=["i3ipc>=2.0.1"],
    extras_require={"dev": ["black", "flake8"],},
    entry_points={"console_scripts": ["i3-quickterm=i3_quickterm:main",],},
    project_urls={
        "Bug Reports": "https://github.com/lbonn/i3-quickterm/issues",
        "Source": "https://github.com/lbonn/i3-quickterm",
    },
)
