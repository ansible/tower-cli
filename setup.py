#!/usr/bin/env python

import os
import sys
from glob import glob

sys.path.insert(0, os.path.abspath('lib'))
from lib import __version__, __author__
from distutils.core import setup

setup(name='ansible',
      version=__version__,
      description='Command line interface to AnsibleWorks AWX',
      author=__author__,
      author_email='michael@ansibleworks.com',
      url='http://ansibleworks.com/',
      license='Apache2',
      install_requires=[],
      package_dir={ 'awx_cli': 'lib/awx_cli' },
      packages=[
         'awx_cli',
         'awx_cli.commands',
      ],
      scripts=[
         'bin/awx-cli',
      ],
      data_files=[]
)
