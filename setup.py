from binascii import rledecode_hqx
from setuptools import setup, find_packages
import os

lib_folder = os.path.dirname(os.path.realpath(__file__))
requirement_path = lib_folder + '/requirements.txt'
requirements = []  # Here we'll get: ["gunicorn", "docutils>=0.3", "lxml==0.5a7"]
if os.path.isfile(requirement_path):
    with open(requirement_path) as fh:
        requirements = fh.read().splitlines()
        requirements = [requirement for requirement in requirements
                        if not requirement.startswith('#')]


print(f'requirements: {requirements}')

SRC_ROOT = "sdwsn_controller"


with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()


setup(
    name='sdwsn_controller',
    version='1.0',
    description='An open source implementation of an SDWSN controller',
    author='Fernando Jurado-Lasso',
    author_email='ffjla@dtu.dk',
    long_description=long_description,
    project_urls={
        'Documentation': 'https://github.com/fdojurado/SDWSN-controller/wiki',
        'Source': 'https://github.com/fdojurado/SDWSN-controller',
        'Tracker': 'https://github.com/fdojurado/SDWSN-controller/issues',
    },
    # packages=['elise'],  # same as name
    install_requires=requirements,
    packages=find_packages(include=['sdwsn_controller', 'sdwsn_controller.*']),
    # packages=['sdwsn_controller', 'sdwsn_controller.tests'],
    # package_dir={'': SRC_ROOT},
    keywords='SDWSN controller SDN WSN',
    python_requires='>=3.10'
)
