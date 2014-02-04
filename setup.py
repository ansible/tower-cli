#!/usr/bin/env python

# Copyright 2013, AnsibleWorks Inc.
# Michael DeHaan <michael@ansibleworks.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import sys
from glob import glob

sys.path.insert(0, os.path.abspath('lib'))
from tower_cli import __version__, __author__
from distutils.core import setup

setup(name='tower_cli',
      version=__version__,
      description='Command line interface to Ansible Tower',
      author=__author__,
      author_email='michael@ansible.com',
      url='http://ansible.com/',
      license='Apache2',
      install_requires=[],
      package_dir={ 'tower_cli': 'lib/tower_cli' },
      packages=[
         'tower_cli',
         'tower_cli.commands',
      ],
      scripts=[
         'bin/tower-cli',
      ],
      data_files=[]
)
