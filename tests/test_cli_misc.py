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

import json
import os.path
import stat
import warnings

import click
from click.testing import CliRunner
from fauxquests.response import Resp
from fauxquests.utils import URL
import requests
import six.moves.urllib.parse as urlparse

import tower_cli
from tower_cli.api import client, Client
from tower_cli.cli.misc import config, version, login, _echo_setting
from tower_cli.conf import settings
from tower_cli.constants import CUR_API_VERSION

from tests.compat import unittest, mock


class VersionTests(unittest.TestCase):
    """A set of tests to ensure that the version command runs in the way
    that we expect.
    """
    def setUp(self):
        self.runner = CliRunner()

    def test_version_command(self):
        """Establish that the version command returns the output we
        expect.
        """
        # Set up output from the /config/ endpoint in Tower and
        # invoke the command.
        with client.test_mode as t:
            t.register_json('/config/', {
                'license_info': {
                    'license_type': 'open'
                },
                'version': '4.21',
                'ansible_version': '2.7'
            })
            result = self.runner.invoke(version)

            # Verify that we got the output we expected.
            self.assertEqual(result.exit_code, 0)
            self.assertEqual(
                result.output.strip(),
                'Tower CLI %s\n'
                'API %s\n'
                'AWX 4.21\n'
                'Ansible 2.7' % (
                    tower_cli.__version__,
                    CUR_API_VERSION
                ),
            )

    def test_cannot_connect(self):
        """Establish that the version command gives a nice error in cases
        where it cannot connect to Tower.
        """
        with mock.patch.object(client, 'get') as get:
            get.side_effect = requests.exceptions.RequestException
            result = self.runner.invoke(version)
            self.assertEqual(result.exit_code, 1)
            self.assertIn('Could not connect to Ansible Tower.', result.output)


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
        with mock.patch('tower_cli.cli.misc.open', mock_open,
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
        with mock.patch('tower_cli.cli.misc.open', mock_open,
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
        with mock.patch('tower_cli.cli.misc.open', mock_open,
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
        with mock.patch('tower_cli.cli.misc.open', mock_open,
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
        with mock.patch('tower_cli.cli.misc.open', mock_open,
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


class LoginTests(unittest.TestCase):
    """Establish that the `tower-cli login` command works in the way
    that we expect.
    """
    def setUp(self):
        self.runner = CliRunner()

    def test_no_arguments(self):
        """
        Establish that if `tower-cli login` is called with no arguments, it
        complains
        """
        # Invoke the command.
        result = self.runner.invoke(login)

        # Ensure that we got a non-zero exit status
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn('Missing argument "username"'.lower(), result.output.lower())

    def test_oauth_unsupported(self):
        """Establish that if `tower-cli login` is used on a Tower that
        doesn't support OAuth2, it shows a meaningful error
        """
        with client.test_mode as t:
            # You have to modify this internal private registry to
            # register a URL endpoint that _doesn't_ have the version
            # prefix
            prefix = Client().get_prefix(include_version=False)
            t._registry[URL(prefix + 'o/', method='HEAD')] = Resp(
                ''.encode('utf-8'), 404, {}
            )
            result = self.runner.invoke(
                login, ['bob', '--password', 'secret']
            )

        # Ensure that we got a non-zero exit status
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn(
            'Error: This version of Tower does not support OAuth2.0',
            result.output
        )

    def test_personal_access_token(self):
        """Establish that if `tower-cli login` is called with a username and
        password, we obtain and write an oauth token to the config file
        """
        # Invoke the command.
        mock_open = mock.mock_open()
        with mock.patch('tower_cli.cli.misc.open', mock_open,
                        create=True):
            with mock.patch.object(os, 'chmod'):
                with client.test_mode as t:
                    # You have to modify this internal private registry to
                    # register a URL endpoint that _doesn't_ have the version
                    # prefix
                    prefix = Client().get_prefix(include_version=False)
                    t._registry[URL(prefix + 'o/', method='HEAD')] = Resp(
                        ''.encode('utf-8'), 200, {}
                    )
                    t.register('/users/bob/personal_tokens/', json.dumps({
                        'token': 'abc123'
                    }), status_code=201, method='POST')
                    result = self.runner.invoke(
                        login, ['bob', '--password', 'secret', '--scope', 'read']
                    )

        # Ensure that we got a zero exit status
        self.assertEqual(result.exit_code, 0)
        assert json.loads(t.requests[-1].body)['scope'] == 'read'

        # Ensure that the output seems to be correct.
        self.assertIn(mock.call(os.path.expanduser('~/.tower_cli.cfg'), 'w'),
                      mock_open.mock_calls)
        self.assertIn(mock.call().write('oauth_token = abc123\n'),
                      mock_open.mock_calls)

    def test_personal_access_invalid(self):
        """Establish that if `tower-cli login` is called with an invalid
        username and password, it shows a meaningful error
        """
        with client.test_mode as t:
            # You have to modify this internal private registry to
            # register a URL endpoint that _doesn't_ have the version
            # prefix
            prefix = Client().get_prefix(include_version=False)
            t._registry[URL(prefix + 'o/', method='HEAD')] = Resp(
                ''.encode('utf-8'), 200, {}
            )
            t.register('/users/bob/personal_tokens/', json.dumps({}),
                       status_code=401, method='POST')
            result = self.runner.invoke(
                login, ['bob', '--password', 'secret']
            )

        # Ensure that we got a non-zero exit status
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn(
            'Error: Invalid Tower authentication credentials', result.output
        )

    def test_application_scoped_token(self):
        """Establish that if `tower-cli login` is called with a username,
        password, and OAuth2 client ID and secret, we obtain and write an oauth
        token to the config file
        """
        # Invoke the command.
        mock_open = mock.mock_open()
        with mock.patch('tower_cli.cli.misc.open', mock_open,
                        create=True):
            with mock.patch.object(os, 'chmod'):
                with client.test_mode as t:
                    # You have to modify this internal private registry to
                    # register a URL endpoint that _doesn't_ have the version
                    # prefix
                    prefix = Client().get_prefix(include_version=False)
                    t._registry[URL(prefix + 'o/', method='HEAD')] = Resp(
                        ''.encode('utf-8'), 200, {}
                    )
                    t._registry[URL(prefix + 'o/token/', method='POST')] = Resp(
                        json.dumps({'access_token': 'abc123'}).encode('utf-8'),
                        201, {}
                    )
                    result = self.runner.invoke(
                        login, ['bob', '--password', 'secret', '--client-id',
                                'abc123', '--client-secret', 'some-secret']
                    )

        # Ensure that we got a zero exit status
        self.assertEqual(result.exit_code, 0)
        data = urlparse.parse_qs(t.requests[-1].body)
        assert data['scope'] == ['write']
        assert data['grant_type'] == ['password']
        assert data['password'] == ['secret']
        assert data['username'] == ['bob']

        # Ensure that the output seems to be correct.
        self.assertIn(mock.call(os.path.expanduser('~/.tower_cli.cfg'), 'w'),
                      mock_open.mock_calls)
        self.assertIn(mock.call().write('oauth_token = abc123\n'),
                      mock_open.mock_calls)

    def test_public_application_scoped_token(self):
        """Establish that if `tower-cli login` is called with a username,
        password, and public OAuth2 client ID, we obtain and write an oauth
        token to the config file
        """
        # Invoke the command.
        mock_open = mock.mock_open()
        with mock.patch('tower_cli.cli.misc.open', mock_open,
                        create=True):
            with mock.patch.object(os, 'chmod'):
                with client.test_mode as t:
                    # You have to modify this internal private registry to
                    # register a URL endpoint that _doesn't_ have the version
                    # prefix
                    prefix = Client().get_prefix(include_version=False)
                    t._registry[URL(prefix + 'o/', method='HEAD')] = Resp(
                        ''.encode('utf-8'), 200, {}
                    )
                    t._registry[URL(prefix + 'o/token/', method='POST')] = Resp(
                        json.dumps({'access_token': 'abc123'}).encode('utf-8'),
                        201, {}
                    )
                    result = self.runner.invoke(
                        login, ['bob', '--password', 'secret', '--client-id',
                                'abc123']
                    )

        # Ensure that we got a zero exit status
        self.assertEqual(result.exit_code, 0)
        data = urlparse.parse_qs(t.requests[-1].body)
        assert data['scope'] == ['write']
        assert data['grant_type'] == ['password']
        assert data['password'] == ['secret']
        assert data['username'] == ['bob']
        assert data['client_id'] == ['abc123']

        # Ensure that the output seems to be correct.
        self.assertIn(mock.call(os.path.expanduser('~/.tower_cli.cfg'), 'w'),
                      mock_open.mock_calls)
        self.assertIn(mock.call().write('oauth_token = abc123\n'),
                      mock_open.mock_calls)


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
                _echo_setting('host')
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
        with mock.patch('tower_cli.cli.misc.open', mock_open,
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
