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

import os
import os.path
import stat
import warnings

from six.moves import StringIO

from tower_cli.conf import Parser, Settings, runtime_context_manager

from tests.compat import unittest, mock


class SettingsTests(unittest.TestCase):
    """A set of tests to establish that our settings object works in
    the way that we expect.
    """
    def test_error_etc_awx(self):
        """Establish that if /etc/tower/ exists but isn't readable,
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
                        settings
                        warn.assert_called_once_with(
                            '/etc/tower/ is present, but not readable with '
                            'current permissions. Any settings defined in '
                            '/etc/tower/tower_cli.cfg will not be honored.',
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

    def test_file_permission_warning(self):
        """Warn file permissions may expose credentials
        """
        with mock.patch.object(warnings, 'warn') as warn:
            with mock.patch.object(os.path, 'isfile') as isfile:
                with mock.patch.object(os, 'stat') as os_stat:
                    isfile.return_value = True
                    mock_stat = type('statobj', (), {})()  # placeholder object
                    mock_stat.st_mode = stat.S_IRUSR | stat.S_IWUSR | \
                        stat.S_IROTH
                    os_stat.return_value = mock_stat  # readable to others
                    parser = Parser()
                    read_file_method = getattr(parser, 'read_file',
                                               parser.readfp)
                    read_file_method(StringIO('[general]\nfoo: bar\n'))
                    warn.assert_called_once_with(mock.ANY, RuntimeWarning)
        # Also run with acceptable permissions, verify that no warning issued
        with mock.patch.object(warnings, 'warn') as warn:
            with mock.patch.object(os.path, 'isfile') as isfile:
                with mock.patch.object(os, 'stat') as os_stat:
                    isfile.return_value = True
                    mock_stat = type('statobj', (), {})()  # placeholder object
                    mock_stat.st_mode = stat.S_IRUSR | stat.S_IWUSR
                    os_stat.return_value = mock_stat  # not readable to others
                    parser = Parser()
                    read_file_method = getattr(parser, 'read_file',
                                               parser.readfp)
                    read_file_method(StringIO('[general]\nfoo: bar\n'))
                    assert not warn.called


class ConfigFromEnvironmentTests(unittest.TestCase):
    """A set of tests that ensure the environment from config
    parsing works as intended.
    """
    def test_no_override(self):
        """Establish that the environment variables do not override explicitly
        passed in values."""
        settings = Settings()
        with mock.patch.dict(os.environ, {'TOWER_HOST': 'myhost'}):
            with settings.runtime_values(host='yourhost'):
                self.assertEqual(settings.host, 'yourhost')

    def test_read_from_env(self):
        """Establish that the environment variables are correctly parsed
        and the values are set in the settings."""
        settings = Settings()

        mock_env = {'TOWER_HOST': 'myhost', 'TOWER_PASSWORD': 'mypass',
                    'TOWER_USERNAME': 'myuser', 'TOWER_VERIFY_SSL': 'False'}

        with mock.patch.dict(os.environ, mock_env):
            with settings.runtime_values():
                self.assertEqual(settings.host, 'myhost')
                self.assertEqual(settings.username, 'myuser')
                self.assertEqual(settings.password, 'mypass')
                self.assertEqual(settings.verify_ssl, False)


class CommandTests(unittest.TestCase):
    """Establish that the @command decorator works as I expect,
    with and without a call signature.
    """
    def test_command_with_call_signature(self):
        """Establish that if we call the @click.command decorator with a call
        signature, that it decorates the function appropriately.
        """
        # Define a command
        @click.command()
        def foo():
            pass

        # Ensure that it's a command.
        self.assertIsInstance(foo, click.core.Command)

    def test_runtime_context_manager(self):
        """Test that the kwargs from settings are removed before
        running the command from the resource itself.
        """
        def foo(**kwargs):
            self.assertEqual(kwargs, {})

        foo = runtime_context_manager(foo)
        foo(tower_username='foobear')
