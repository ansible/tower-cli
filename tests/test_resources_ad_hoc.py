# Copyright 2015, Ansible, Inc.
# Alan Rominger <arominger@ansible.com>
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

import tower_cli
from tower_cli.api import client
from tower_cli.utils import exceptions as exc

from tests.compat import unittest, mock
from tower_cli.conf import settings
import json

import click


class LaunchTests(unittest.TestCase):
    """A set of tests for ensuring that the ad hoc resource's
    launch command works in the way we expect.
    """
    def setUp(self):
        self.res = tower_cli.get_resource('ad_hoc')

    def test_basic_launch(self):
        """Establish that we are able to run an ad hoc command.
        """
        with client.test_mode as t:
            t.register_json('/ad_hoc_commands/42/', {'id': 42}, method='GET')
            t.register_json('/', {
                'ad_hoc_commands': '/api/v1/ad_hoc_commands/'
                }, method='GET')
            t.register_json('/ad_hoc_commands/', {'id': 42}, method='POST')
            result = self.res.launch(inventory="foobar", machine_credential=2)
            self.assertEqual(result, {'changed': True, 'id': 42})

    def test_launch_with_become(self):
        """Establish that we are able use the --become flag
        """
        with client.test_mode as t:
            t.register_json('/ad_hoc_commands/42/', {'id': 42}, method='GET')
            t.register_json('/', {
                'ad_hoc_commands': '/api/v1/ad_hoc_commands/'
                }, method='GET')
            t.register_json('/ad_hoc_commands/', {'id': 42}, method='POST')
            self.res.launch(inventory="foobar", machine_credential=2,
                            become=True)
            # Critically, we test that the request sent to the server
            # contains the key "become_enabled", as this must be triggered
            # by the conditional written specifically for --become
            self.assertDictContainsSubset(
                {'become_enabled': True},
                json.loads(t.requests[1].body)
            )

    def test_basic_launch_with_echo(self):
        """Establish that we are able to run an ad hoc command and also
        print that to the command line without errors.
        """
        with client.test_mode as t:
            t.register_json('/ad_hoc_commands/42/', {'id': 42}, method='GET')
            t.register_json('/', {
                'ad_hoc_commands': '/api/v1/ad_hoc_commands/'
                }, method='GET')
            t.register_json(
                '/ad_hoc_commands/',
                {'changed': True, 'id': 42,
                    'inventory': 'foobar', 'credential': 2,
                    'name': 'ping', 'created': 1234, 'elapsed': 2352,
                    'status': 'successful', 'module_name': 'command',
                    'limit': '', }, method='POST'
            )
            result = self.res.launch(inventory="foobar", machine_credential=2)
            self.assertEqual(result['changed'], True)
            self.assertEqual(result['id'], 42)

            f = self.res.as_command()._echo_method(self.res.launch)
            with mock.patch.object(click, 'secho'):
                with settings.runtime_values(format='human'):
                    f(inventory="foobar", machine_credential=2)

    def test_launch_with_param(self):
        """Establish that we are able to run an ad hoc command.
        """
        with client.test_mode as t:
            t.register_json('/ad_hoc_commands/42/', {'id': 42}, method='GET')
            t.register_json('/', {
                'ad_hoc_commands': '/api/v1/ad_hoc_commands/'
                }, method='GET')
            t.register_json('/ad_hoc_commands/', {'id': 42}, method='POST')
            result = self.res.launch(inventory="foobar", machine_credential=2,
                                     module_args="echo 'hi'")
            self.assertEqual(result, {'changed': True, 'id': 42})

    def test_version_failure(self):
        """Establish that if the command has failed, that we raise the
        JobFailure exception.
        """
        with client.test_mode as t:
            t.register_json('/ad_hoc_commands/42/', {'id': 42}, method='GET')
            t.register_json('/', {}, method='GET')
            t.register_json('/ad_hoc_commands/', {'id': 42}, method='POST')
            with self.assertRaises(exc.TowerCLIError):
                self.res.launch(inventory=1, machine_credential=2,
                                module_args="echo 'hi'")

    def test_basic_launch_monitor_option(self):
        """Establish that we are able to run a command and monitor
        it, if requested.
        """
        with client.test_mode as t:
            t.register_json('/ad_hoc_commands/42/', {'id': 42}, method='GET')
            t.register_json('/', {
                'ad_hoc_commands': '/api/v1/ad_hoc_commands/'
                }, method='GET')
            t.register_json('/ad_hoc_commands/', {'id': 42}, method='POST')

            with mock.patch.object(type(self.res), 'monitor') as monitor:
                self.res.launch(inventory=1, machine_credential=2,
                                module_args="echo 'hi'", monitor=True)
                monitor.assert_called_once_with(42, timeout=None)


class StatusTests(unittest.TestCase):
    """A set of tests to establish that the ad hoc job status command
    works in the way that we expect.
    """
    def setUp(self):
        self.res = tower_cli.get_resource('ad_hoc')

    def test_normal(self):
        """Establish that the data about an ad hoc command retrieved
        from the jobs endpoint is provided.
        """
        with client.test_mode as t:
            t.register_json('/ad_hoc_commands/42/', {
                'elapsed': 1335024000.0,
                'extra': 'ignored',
                'failed': False,
                'status': 'successful',
            })
            result = self.res.status(42)
            self.assertEqual(result, {
                'elapsed': 1335024000.0,
                'failed': False,
                'status': 'successful',
            })
            self.assertEqual(len(t.requests), 1)

    def test_detailed(self):
        with client.test_mode as t:
            t.register_json('/ad_hoc_commands/42/', {
                'elapsed': 1335024000.0,
                'extra': 'ignored',
                'failed': False,
                'status': 'successful',
            })
            result = self.res.status(42, detail=True)
            self.assertEqual(result, {
                'elapsed': 1335024000.0,
                'extra': 'ignored',
                'failed': False,
                'status': 'successful',
            })
            self.assertEqual(len(t.requests), 1)


class CancelTests(unittest.TestCase):
    """A set of tasks to establish that the ad hoc cancel
    command works in the way that we expect.
    """
    def setUp(self):
        self.res = tower_cli.get_resource('ad_hoc')

    def test_standard_cancelation(self):
        """Establish that a standard cancelation command works in the way
        we expect.
        """
        with client.test_mode as t:
            t.register('/ad_hoc_commands/42/cancel/', '', method='POST')
            result = self.res.cancel(42)
            self.assertTrue(
                t.requests[0].url.endswith('/ad_hoc_commands/42/cancel/')
            )
            self.assertTrue(result['changed'])

    def test_cancelation_completed_with_error(self):
        """Establish that a standard cancelation command works in the way
        we expect.
        """
        with client.test_mode as t:
            t.register('/ad_hoc_commands/42/cancel/', '',
                       method='POST', status_code=405)
            with self.assertRaises(exc.TowerCLIError):
                self.res.cancel(42, fail_if_not_running=True)
