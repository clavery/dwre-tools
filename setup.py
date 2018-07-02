#!/usr/bin/env python

from setuptools import setup, find_packages


def get_requirements(env):
    with open('requirements-{}.txt'.format(env)) as fp:
        return [x.strip() for x in fp.read().split('\n') if not x.startswith('#') and x.strip()]


install_requires = get_requirements('base')
test_requires = get_requirements('test')
dev_requires = get_requirements('dev')
setup(
    name='dwre-tools',
    version='1.13.6',
    description='SFCC (Demandware) tools',
    author='Charles Lavery',
    author_email='clavery@pixelmedia.com',
    url='https://bitbucket.org/pixelmedia/dwre-dwre-tools',
    packages=find_packages(),
    include_package_data=True,
    test_suite='pytest-runner',
    tests_require=test_requires,
    setup_requires=['pytest-runner'],
    install_requires=install_requires,
    dependency_links=[
        'git+https://github.com/yaml/pyyaml.git@0124e4cf9fe0c5814f43592494279edeef67994e#egg=pyyaml-4.2.0'
    ],
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
