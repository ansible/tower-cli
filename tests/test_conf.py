# Copyright 2014, Ansible, Inc.
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

import os
import os.path
import warnings

from six.moves import StringIO

from tower_cli.conf import Parser, Settings

from tests.compat import unittest, mock


class SettingsTests(unittest.TestCase):
    """A set of tests to establish that our settings object works in
    the way that we expect.
    """
    def test_error_etc_awx(self):
        """Establish that if /etc/awx/ exists but isn't readable,
        that we properly catch it and whine about it.
        """
        with mock.patch.object(os, 'getcwd') as getcwd:
            getcwd.return_value = os.path.expanduser('~')
            with mock.patch.object(warnings, 'warn') as warn:
                with mock.patch.object(os.path, 'isdir') as isdir:
                    isdir.return_value = True
                    with mock.patch.object(os, 'listdir') as listdir:
                        listdir.side_effect = OSError
                        settings = Settings()
                        warn.assert_called_once_with(
                            '/etc/awx/ is present, but not readable with '
                            'current permissions. Any settings defined in '
                            '/etc/awx/tower_cli.cfg will not be honored.',
                            RuntimeWarning,
                        )


class ParserTests(unittest.TestCase):
    """A set of tests to establish that our Parser subclass works in the
    way that we expect.
    """
    def test_parser_read_with_header(self):
        """Establish that the parser can read settings with a standard
        header.
        """
        parser = Parser()
        read_file_method = getattr(parser, 'read_file', parser.readfp)
        read_file_method(StringIO('[general]\nfoo: bar\n'))
        self.assertEqual(parser.get('general', 'foo'), 'bar')

    def test_parser_read_without_header(self):
        """Establish that the parser can read settings without a
        standard header, and that "general" is then implied.
        """
        parser = Parser()
        read_file_method = getattr(parser, 'read_file', parser.readfp)
        read_file_method(StringIO('foo: bar'))
        self.assertEqual(parser.get('general', 'foo'), 'bar')
