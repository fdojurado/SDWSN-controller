from setuptools import setup

setup(
   name='controller',
   version='1.0',
   description='An SDN controller for contiki',
   author='Fernando Jurado',
   author_email='fjurado@student.unimelb.edu.au',
   packages=['controller'],  #same as name
   install_requires=['bar', 'greek'], #external packages as dependencies
)