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
    name='analytics',
    version='0.0.1',
    description="Set of analytics reports",
    long_description="""Set of analytics reports""",
    license="http://www.apache.org/licenses/LICENSE-2.0",
    classifiers=[
        "License :: OSI Approved :: Apache Software License",
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python",
    ],
    author='Mirantis Inc.',
    author_email='product@mirantis.com',
    url='https://mirantis.com',
    keywords='fuel statistics collector mirantis',
    packages=find_packages(),
    zip_safe=False,
    install_requires=parse_requirements_txt(),
    include_package_data=True,
    scripts=[]
)
