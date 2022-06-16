from importlib import import_module
from pathlib import Path
from setuptools import setup, find_packages

SRC_ROOT = 'src'

about = import_module(SRC_ROOT + '.about')


# with Path('README.md').open('r') as fh:
#     long_description = fh.read()

with Path('requirements.txt').open('r') as fh:
    requirements = fh.read().splitlines()
    requirements = [requirement for requirement in requirements
                    if not requirement.startswith('#')]

setup(
    name=about.PROJECT,
    version=about.VERSION,
    description=about.DESCRIPTION,
    author=about.AUTHOR,
    author_email=about.EMAIL,
    project_urls={
        'Documentation': about.DOC_URL,
        'Source': about.GITHUB_URL,
        'Tracker': about.TRACKER_URL,
    },
    # packages=['controller'],  # same as name
    install_requires=requirements,
    packages=find_packages('src'),
    package_dir={'': SRC_ROOT},
    python_requires='>=3.10',
    keywords=about.KEYWORDS
)
