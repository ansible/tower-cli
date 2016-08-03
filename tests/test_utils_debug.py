# Copyright 2015, Ansible, Inc.
# Luke Sneeringer <lsneeringer@ansible.com>
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

import click

from tower_cli.conf import settings
from tower_cli.utils import debug

from tests.compat import unittest, mock


class LogTests(unittest.TestCase):
    """A set of tests to establish that the log method works in the way
    that we expect.
    """
    def test_not_verbose_mode(self):
        """Establish that this method does nothing if we are not in
        verbose mode.
        """
        with settings.runtime_values(verbose=False):
            with mock.patch.object(click, 'secho') as secho:
                debug.log('foo bar baz')
                self.assertEqual(secho.call_count, 0)

    def test_header(self):
        """Establish that a header echoes the expected string, of
        correct length.
        """
        s = 'Decided all the things.'
        with mock.patch.object(click, 'secho') as secho:
            with settings.runtime_values(verbose=True):
                debug.log(s, header='decision', fg='blue')
            self.assertEqual(secho.mock_calls[0][1][0],
                             '*** DECISION: Decided all the things. '
                             '*****************************************')

    def test_extra_newlines(self):
        """Establish that extra newlines are correctly applied if they
        are requested.
        """
        s = 'All your base are belong to us.'
        with mock.patch.object(click, 'secho') as secho:
            with settings.runtime_values(verbose=True):
                debug.log(s, nl=3)
            self.assertEqual(secho.mock_calls[0][1][0],
                             'All your base are belong to us.\n\n')

    def test_multi_lines(self):
        """Establish that overly long debug messages will be displayed in
        multiple lines.
        """
        s = ' '.join(['multi-line'] * 30)
        expected = '\n'.join([
            '*** DETAILS: multi-line multi-line multi-line '
            'multi-line multi-line multi-line ',
            '*** multi-line multi-line multi-line multi-line '
            'multi-line multi-line *********',
            '*** multi-line multi-line multi-line multi-line '
            'multi-line multi-line *********',
            '*** multi-line multi-line multi-line multi-line '
            'multi-line multi-line *********',
            '*** multi-line multi-line multi-line multi-line '
            'multi-line multi-line *********',
        ])
        with mock.patch.object(click, 'secho') as secho:
            with settings.runtime_values(verbose=True):
                debug.log(s, header='details')
            self.assertEqual(secho.mock_calls[0][1][0], expected)
