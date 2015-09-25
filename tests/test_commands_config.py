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

import os.path
import stat
import warnings

import click
from click.testing import CliRunner

from tower_cli.commands.config import config, echo_setting
from tower_cli.conf import settings

from tests.compat import unittest, mock


class ConfigTests(unittest.TestCase):
    """Establish that the `tower-cli config` command works in the way
    that we expect.
    """
    def setUp(self):
        self.runner = CliRunner()

    def test_no_arguments(self):
        """Establish that if `tower-cli config` is called with no arguments,
        that we print out the current configuration.
        """
        # Invoke the command.
        with settings.runtime_values(username='meagan', verbose=False,
                                     password='This is the best wine.'):
            result = self.runner.invoke(config)

        # Ensure that we got a 0 exit status
        self.assertEqual(result.exit_code, 0)

        # Ensure that the output looks correct.
        self.assertIn('username: meagan', result.output)
        self.assertIn('password: This is the best wine.', result.output)
        self.assertIn('verbose: False', result.output)

    def test_key_and_no_value(self):
        """Establish that if we are given a key and no value, that the
        setting's value is printed.
        """
        with settings.runtime_values(password='This is the best wine.'):
            result = self.runner.invoke(config, ['password'])
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.output.strip(),
                         'password: This is the best wine.')

    def test_write_setting(self):
        """Establish that if we attempt to write a valid setting, that
        the parser's write method is run.
        """
        # Invoke the command, but trap the file-write at the end
        # so we don't plow over real things.
        mock_open = mock.mock_open()
        filename = os.path.expanduser('~/.tower_cli.cfg')
        with mock.patch('tower_cli.commands.config.open', mock_open,
                        create=True):
            with mock.patch.object(os, 'chmod') as chmod:
                result = self.runner.invoke(config, ['username', 'luke'])
                chmod.assert_called_once_with(filename, int('0600', 8))

        # Ensure that the command completed successfully.
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.output.strip(),
                         'Configuration updated successfully.')

        # Ensure that the output seems to be correct.
        self.assertIn(mock.call(os.path.expanduser('~/.tower_cli.cfg'), 'w'),
                      mock_open.mock_calls)
        self.assertIn(mock.call().write('username = luke\n'),
                      mock_open.mock_calls)

    def test_permissions_warning(self):
        """Warn user if configuration file permissions can not be set
        """
        # Try to set permissions on file that does not exist, expecting warning
        mock_open = mock.mock_open()
        filename = '.tower_cli.cfg'
        with mock.patch('tower_cli.commands.config.open', mock_open,
                        create=True):
            with mock.patch.object(os, 'chmod') as chmod:
                chmod.side_effect = OSError
                with mock.patch.object(warnings, 'warn') as warn:
                    result = self.runner.invoke(
                        config, ['username', 'luke', '--scope=local'])
                    warn.assert_called_once_with(mock.ANY, UserWarning)
                    chmod.assert_called_once_with(
                        filename, stat.S_IRUSR | stat.S_IWUSR)

        # Ensure that the command completed successfully.
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.output.strip(),
                         'Configuration updated successfully.')

    def test_write_global_setting(self):
        """Establish that if we attempt to write a valid setting, that
        the parser's write method is run.
        """
        # Invoke the command, but trap the file-write at the end
        # so we don't plow over real things.
        filename = '/etc/tower/tower_cli.cfg'
        mock_open = mock.mock_open()
        with mock.patch('tower_cli.commands.config.open', mock_open,
                        create=True):
            with mock.patch.object(os.path, 'isdir') as isdir:
                with mock.patch.object(os, 'chmod') as chmod:
                    isdir.return_value = True
                    result = self.runner.invoke(
                        config, ['username', 'luke', '--scope=global'],
                    )
                    isdir.assert_called_once_with('/etc/tower/')
                    chmod.assert_called_once_with(filename, int('0600', 8))

        # Ensure that the command completed successfully.
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.output.strip(),
                         'Configuration updated successfully.')

        # Ensure that the output seems to be correct.
        self.assertIn(mock.call('/etc/tower/tower_cli.cfg', 'w'),
                      mock_open.mock_calls)
        self.assertIn(mock.call().write('username = luke\n'),
                      mock_open.mock_calls)

    def test_write_local_setting(self):
        """Establish that if we attempt to write a valid setting locally, that
        the correct parser's write method is run.
        """
        # Invoke the command, but trap the file-write at the end
        # so we don't plow over real things.
        mock_open = mock.mock_open()
        with mock.patch('tower_cli.commands.config.open', mock_open,
                        create=True):
            with mock.patch.object(os, 'chmod') as chmod:
                result = self.runner.invoke(
                    config, ['username', 'meagan', '--scope=local'],
                )
                filename = ".tower_cli.cfg"
                chmod.assert_called_once_with(filename, int('0600', 8))

        # Ensure that the command completed successfully.
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.output.strip(),
                         'Configuration updated successfully.')

        # Ensure that the output seems to be correct.
        self.assertIn(mock.call('.tower_cli.cfg', 'w'),
                      mock_open.mock_calls)
        self.assertIn(mock.call().write('username = meagan\n'),
                      mock_open.mock_calls)

    def test_unset(self):
        """Establish that calling `tower-cli config --unset` works in the
        way that we expect.
        """
        # Invoke the command, but trap the file-write at the end
        # so we don't plow over real things.
        mock_open = mock.mock_open()
        with mock.patch('tower_cli.commands.config.open', mock_open,
                        create=True):
            with mock.patch.object(os, 'chmod'):
                result = self.runner.invoke(config, ['username', '--unset'])

        # Ensure that the command completed successfully.
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.output.strip(),
                         'Configuration updated successfully.')

        # Ensure that the output seems to be correct.
        self.assertNotIn(mock.call().write('username = luke\n'),
                         mock_open.mock_calls)

    def test_error_invalid_key(self):
        """Establish that if `tower-cli config` is sent an invalid key,
        that we raise an exception.
        """
        result = self.runner.invoke(config, ['bogus'])
        self.assertEqual(result.exit_code, 1)
        self.assertEqual(result.output.strip(),
                         'Error: Invalid configuration option "bogus".')

    def test_error_value_and_unset(self):
        """Establish that if `tower-cli config` is called with both a value
        and the --unset flag, that we raise an exception.
        """
        result = self.runner.invoke(config, ['host', '127.0.0.1', '--unset'])
        self.assertEqual(result.exit_code, 2)
        self.assertEqual(result.output.strip(),
                         'Error: Cannot provide both a value and --unset.')

    def test_error_no_global_config_file(self):
        """Establish that if no global config file exists, that tower-cli
        does not attempt to create it.
        """
        with mock.patch.object(os.path, 'isdir') as isdir:
            isdir.return_value = False
            result = self.runner.invoke(config,
                                        ['host', 'foo', '--scope=global'])
            isdir.assert_called_once_with('/etc/tower/')
        self.assertEqual(result.exit_code, 1)
        self.assertEqual(result.output.strip(),
                         'Error: /etc/tower/ does not exist, and this '
                         'command cowardly declines to create it.')


class SupportTests(unittest.TestCase):
    """Establish that support functions in this module work in the way
    that we expect.
    """
    def test_echo_setting(self):
        """Establish that the `echo_setting` method works in the way
        that we expect.
        """
        with settings.runtime_values(host='20.12.4.21'):
            with mock.patch.object(click, 'secho') as secho:
                echo_setting('host')
                self.assertEqual(secho.mock_calls, [
                    mock.call('host: ', fg='magenta', bold=True, nl=False),
                    mock.call('20.12.4.21', fg='white', bold=True),
                ])


class DeprecationTests(unittest.TestCase):
    """Establish any deprecation notices are sent with a command if they
    are expected.
    """
    def setUp(self):
        self.runner = CliRunner()

    def test_write_global_setting_deprecated(self):
        """Establish that if we attempt to write a valid setting, that
        the parser's write method is run.
        """
        # Invoke the command, but trap the file-write at the end
        # so we don't plow over real things.
        mock_open = mock.mock_open()
        warning_text = 'The `--global` option is deprecated and will be '\
                       'removed. Use `--scope=global` to get the same effect.'
        with mock.patch('tower_cli.commands.config.open', mock_open,
                        create=True):
            with mock.patch.object(os.path, 'isdir') as isdir:
                with mock.patch.object(os, 'chmod'):
                    with mock.patch.object(warnings, 'warn') as warn:
                        isdir.return_value = True
                        result = self.runner.invoke(
                            config, ['username', 'meagan', '--global'],
                        )
                        warn.assert_called_once_with(warning_text,
                                                     DeprecationWarning)
                        self.assertEqual(warn.mock_calls[0][1][1],
                                         DeprecationWarning)
                        isdir.assert_called_once_with('/etc/tower/')

        # Ensure that the command completed successfully.
        self.assertEqual(result.exit_code, 0)
        self.assertEqual('Configuration updated successfully.',
                         result.output.strip())

        # Ensure that the output seems to be correct.
        self.assertIn(mock.call('/etc/tower/tower_cli.cfg', 'w'),
                      mock_open.mock_calls)
        self.assertIn(mock.call().write('username = meagan\n'),
                      mock_open.mock_calls)
