#!/usr/bin/env python

import os
import sys

try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup, find_packages

setup(
    name='dwre-tools',
    version='1.6.8',
    description='SFCC (Demandware) tools',
    author='Charles Lavery',
    author_email='clavery@pixelmedia.com',
    url='https://bitbucket.org/pixelmedia/dwre-dwre-tools',
    packages=find_packages(),
    include_package_data=True,
    install_requires=['requests == 2.7.0',
                      'colorama >= 0.3.3',
                      'pyquery >= 1.2.9',
                      'pytz==2016.10',
                      'lxml >= 3.4.4',
                      'pyyaml >= 3.11',
                      'flask == 0.10.1',
                      'prompt_toolkit == 1.0.13',
                      'terminaltables == 3.1.0',
                      'Pygments == 2.1.3',
                      'wcwidth == 0.1.7',
                      'six >= 1.10.0',
                      ],
    license='MIT License',
    zip_safe=False,
    classifiers=(
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7'
    ),
    entry_points = {
        'console_scripts': ['dwre = dwre_tools.cli:main'],
    },
)
