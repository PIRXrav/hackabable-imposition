# pylint: disable=missing-function-docstring, missing-module-docstring

import codecs
import os.path
import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

INIT_PATH = "hackimposition/__init__.py"
REQ_PATH = "requirements.txt"

# https://packaging.python.org/guides/single-sourcing-package-version/
def read(rel_path):
    here = os.path.abspath(os.path.dirname(__file__))
    with codecs.open(os.path.join(here, rel_path), 'r') as fp:
        return fp.read()

def extract(definition):
    for line in read(INIT_PATH).splitlines():
        if line.startswith(definition):
            delim = '"' if '"' in line else "'"
            return line.split(delim)[1]
    raise RuntimeError("Unable to find version string.")

with open(REQ_PATH) as f:
    required = f.read().splitlines()


setuptools.setup(
    name="hackimposition",
    version=extract('__VERSION__'),
    author=extract('__AUTHOR__'),
    # author_email="author@example.com",
    description=extract('__DESCRIPTION__'),
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/PIRXrav/hackabable-imposition",
    license=extract('__COPYRIGHT__'),
    entry_points={"console_scripts": ["hackimposition = hackimposition.__main__:main"]},
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: OS Independent",
        "Topic :: Printing",
        "Topic :: Software Development :: Libraries :: Python Modules"
    ],
    install_requires=required,
    python_requires='>=3.6',
)
