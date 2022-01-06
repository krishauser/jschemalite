from setuptools import setup

# read the contents of your README file
from os import path
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='jschemalite',
    version='0.1',
    packages=['jschemalite'],
    url='https://www.github.com/krishauser/jschemalite',
    license='Apache 2.0',
    author='Kris Hauser',
    author_email='hauser.kris@gmail.com',
    description='JSON Schema Lite',
    install_requires=[],
    long_description=long_description,
    long_description_content_type='text/markdown',
)
