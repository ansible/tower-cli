#!/usr/bin/env python
# Copyright 2013-2015, Ansible, Inc.
# Michael DeHaan <michael@ansible.com>
# Luke Sneeringer <lsneeringer@ansible.com>
# and others
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

import re
import sys
from distutils.core import setup
from setuptools import find_packages
from setuptools.command.test import test as TestCommand


class Tox(TestCommand):
    """The test command should install and then run tox.

    Based on http://tox.readthedocs.org/en/latest/example/basic.html
    """
    user_options = [('tox-args=', 'a', "Arguments to pass to tox")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.tox_args = ""

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import tox  # Import here, because outside eggs aren't loaded.
        import shlex
        sys.exit(tox.cmdline(args=shlex.split(self.tox_args)))


def parse_requirements(filename):
    """Parse out a list of requirements from the given requirements
    requirements file.
    """
    reqs = []
    version_spec_in_play = None

    # Iterate over each line in the requirements file.
    for line in open(filename, 'r').read().strip().split('\n'):
        # Sanity check: Is this an empty line?
        # If so, do nothing.
        if not line.strip():
            continue

        # If this is just a plain requirement (not a comment), then
        # add it to the requirements list.
        if not line.startswith('#'):
            reqs.append(line)
            continue

        # "Header" comments take the form of "=== Python {op} {version} ===",
        # and make the requirement only matter for those versions.
        # If this line is a header comment, parse it.
        match = re.search(r'^# === [Pp]ython (?P<op>[<>=]{1,2}) '
                          r'(?P<major>[\d])\.(?P<minor>[\d]+) ===[\s]*$', line)
        if match:
            version_spec_in_play = match.groupdict()
            for key in ('major', 'minor'):
                version_spec_in_play[key] = int(version_spec_in_play[key])
            continue

        # If this is a comment that otherwise looks like a package, then it
        # should be a package applying only to the current version spec.
        #
        # We can identify something that looks like a package by a lack
        # of any spaces.
        if ' ' not in line[1:].strip() and version_spec_in_play:
            package = line[1:].strip()

            # Sanity check: Is our version of Python one of the ones currently
            # in play?
            op = version_spec_in_play['op']
            vspec = (version_spec_in_play['major'],
                     version_spec_in_play['minor'])
            if '=' in op and sys.version_info[0:2] == vspec:
                reqs.append(package)
            elif '>' in op and sys.version_info[0:2] > vspec:
                reqs.append(package)
            elif '<' in op and sys.version_info[0:2] < vspec:
                reqs.append(package)

    # Okay, we should have an entire list of requirements now.
    return reqs


def combine_files(*args):
    """returns a string of all the strings in *args combined together,
    with two line breaks between them"""
    file_contents = []
    for filename in args:
        with open(filename, 'r') as f:
            file_contents.append(f.read())
    return "\n\n".join(file_contents)


setup(
    # Basic metadata
    name='ansible-tower-cli',
    version=open('VERSION').read().strip(),
    author='Luke Sneeringer',
    author_email='lsneeringer@ansible.com',
    url='https://github.com/ansible/tower-cli',

    # Additional information
    description='A CLI tool for Ansible Tower.',
    long_description=combine_files('README.rst', 'HISTORY.rst'),
    license='Apache 2.0',

    # How to do the install
    install_requires=parse_requirements('requirements.txt'),
    provides=[
        'tower_cli',
    ],
    scripts=[
        'bin/tower-cli',
    ],
    packages=find_packages(),

    # How to do the tests
    tests_require=['tox'],
    cmdclass={'test': Tox},

    # Data files
    package_data={
        'tower_cli': ['VERSION'],
    },

    # PyPI metadata.
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: System :: Software Distribution',
        'Topic :: System :: Systems Administration',
    ],
)
