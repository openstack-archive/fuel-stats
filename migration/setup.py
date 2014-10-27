#    Copyright 2014 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import os

from setuptools import find_packages
from setuptools import setup


def parse_requirements_txt():
    root = os.path.dirname(os.path.abspath(__file__))
    requirements = []
    with open(os.path.join(root, 'requirements.txt'), 'r') as f:
        for line in f.readlines():
            line = line.rstrip()
            if not line or line.startswith('#'):
                continue
            requirements.append(line)
    return requirements


setup(
    name='migration',
    version='0.0.1',
    description="Statistics data migration tool",
    long_description="""Statistics data migration tool""",
    license="http://www.apache.org/licenses/LICENSE-2.0",
    classifiers=[
        "License :: OSI Approved :: Apache Software License",
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python",
        "Environment :: Console"
    ],
    author='Mirantis Inc.',
    author_email='product@mirantis.com',
    url='https://mirantis.com',
    keywords='fuel statistics dataflow etl mirantis',
    packages=find_packages(),
    zip_safe=False,
    install_requires=parse_requirements_txt(),
    include_package_data=True,
    scripts=['manage_migration.py'],
    entry_points={
        'console_scripts': [
            'migration-runner = migration.runner:main'
        ]
    }
)
