#!/usr/bin/env python

import os
from setuptools import setup, find_packages


def get_requirements(env):
    filename = os.path.join(os.path.dirname(__file__), "requirements-%s.txt" % env)
    with open(filename) as fp:
        return [x.strip() for x in fp.read().split('\n') if not x.startswith('#') and x.strip()]


install_requires = get_requirements('base')
test_requires = get_requirements('test')
dev_requires = get_requirements('dev')

# remove requirement for keyring on linux due to build requirements (rust, etc)
from sys import platform
if platform.startswith("linux"):
    install_requires = [r for r in install_requires if "keyring" not in r]

setup(
    name='dwre-tools',
    version='1.19.0',
    description='SFCC (Demandware) tools',
    author='Charles Lavery',
    author_email='clavery@pixelmedia.com',
    url='https://bitbucket.org/pixelmedia/dwre-dwre-tools',
    packages=find_packages(),
    include_package_data=True,
    tests_require=test_requires,
    setup_requires=['pytest-runner'],
    install_requires=install_requires,
    python_requires='>=3.6',
    extras_require={
        'test': test_requires,
        'dev': test_requires + dev_requires
    },
    license='Private',
    zip_safe=False,
    entry_points={
        'console_scripts': ['dwre = dwre_tools.cli:main'],
    },
)
