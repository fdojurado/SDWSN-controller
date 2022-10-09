from binascii import rledecode_hqx
from setuptools import setup, find_packages
import os

lib_folder = os.path.dirname(os.path.realpath(__file__))

SRC_ROOT = "sdwsn_controller"

about = lib_folder + "/"+SRC_ROOT+"/about.py"

exec(open(about).read())

requirement_path = lib_folder + '/requirements.txt'
requirements = []  # Here we'll get: ["gunicorn", "docutils>=0.3", "lxml==0.5a7"]
if os.path.isfile(requirement_path):
    with open(requirement_path) as fh:
        requirements = fh.read().splitlines()
        requirements = [requirement for requirement in requirements
                        if not requirement.startswith('#')]


print(f'requirements: {requirements}')


with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()


setup(
    name=__project_name__,
    version=__version__,
    description=__description__,
    license=__license__,
    author=__author__,
    author_email=__email__,
    url=__github_url__,
    long_description=long_description,
    project_urls={
        'Documentation':__doc_url__ ,
        'Source': __github_url__,
        'Tracker': __tracker_url__,
    },
    # packages=['elise'],  # same as name
    install_requires=requirements,
    packages=find_packages(include=['sdwsn_controller', 'sdwsn_controller.*']),
    # packages=['sdwsn_controller', 'sdwsn_controller.tests'],
    # package_dir={'': SRC_ROOT},
    keywords=__keywords__,
    python_requires='>=3.10'
)
