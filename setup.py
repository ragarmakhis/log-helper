#!/usr/bin/env python

from setuptools import setup, find_packages

# Get metadata without importing the package
with open('log_helper/metadata.py') as metadata_file:
    exec(metadata_file.read())
    metadata = locals()

with open('README.rst') as readme_file:
    readme = readme_file.read()

# with open('HISTORY.rst') as history_file:
#     history = history_file.read()

requirements = [
    'argparse',
    'lxml'
]

setup(
    author=metadata['__author__'],
    author_email=metadata['__email__'],
    url=metadata['__url__'],
    version=metadata['__version__'],
    python_requires='>=3.8',
    description=metadata['__summary__'],
    entry_points={
        'console_scripts': [
            'log_helper=log_helper.cli:main',
        ],
    },
    install_requires=requirements,
    license='MIT license',
    long_description=readme,  # + '\n\n' + history,
    long_description_content_type='text/x-rst',
    include_package_data=True,
    keywords='python video editing helper',
    name='log-helper',
    packages=find_packages(include=['log_helper', 'log_helper.*']),
    # package_data={
    #     'chat_downloader': ['formatting/*.json']
    # },
    # test_suite='tests',
    # zip_safe=False,
)
