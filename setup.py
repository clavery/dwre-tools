#!/usr/bin/env python

import os
import sys

try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup, find_packages

setup(
    name='dwre-tools',
    version='0.0.1',
    description='Simple HTTP server for recording requests and returning arbitrary responses.',
    author='Charles Lavery',
    author_email='charles.lavery@gmail.com',
    url='https://github.com/clavery/reflectme',
    packages=find_packages(),
    include_package_data=True,
    install_requires=['requests==2.4.1',
                      'colorama==0.3.3'],
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
