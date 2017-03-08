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

import tower_cli
from tower_cli.api import client
from tower_cli.utils import exceptions as exc

from tests.compat import unittest, mock


class UpdateTests(unittest.TestCase):
    """A set of tests to establish that the inventory source resource works
    in the way that we expect.
    """
    def setUp(self):
        self.isr = tower_cli.get_resource('inventory_source')

    def test_cannot_sync(self):
        """Establish that if we attempt to update an inventory source that
        cannot be updated, that we raise BadRequest.
        """
        with client.test_mode as t:
            t.register_json('/inventory_sources/1/update/',
                            {'can_update': False}, method='GET')
            with self.assertRaises(exc.BadRequest):
                self.isr.update(1)

    def test_update(self):
        """Establish that if we are able to update an inventory source,
        that the update command does so.
        """
        with client.test_mode as t:
            t.register_json('/inventory_sources/1/update/',
                            {'can_update': True}, method='GET')
            t.register_json('/inventory_sources/1/update/',
                            {}, method='POST')
            answer = self.isr.update(1)
            self.assertEqual(answer['status'], 'ok')

    def test_update_with_monitor(self):
        """Establish that if we call update with the monitor flag, that the
        monitor method runs.
        """
        with client.test_mode as t:
            t.register_json('/inventory_sources/1/update/',
                            {'can_update': True}, method='GET')
            t.register_json('/inventory_sources/1/update/',
                            {'inventory_update': 32}, method='POST')
            t.register_json('/inventory_sources/1/', {'inventory': 1},
                            method='GET')
            with mock.patch.object(type(self.isr), 'monitor') as monitor:
                self.isr.update(1, monitor=True)
                monitor.assert_called_once_with(32, parent_pk=1, timeout=None)
            # Check wait method, following same pattern
            with mock.patch.object(type(self.isr), 'wait') as wait:
                self.isr.update(1, wait=True)
                wait.assert_called_once_with(32, parent_pk=1, timeout=None)


class StatusTests(unittest.TestCase):
    """A set of tests to establish that the inventory_source status command
    works in the way that we expect.
    """
    def setUp(self):
        self.res = tower_cli.get_resource('inventory_source')
        self.detail_uri = '/inventory_sources/1/inventory_updates/42/'

    def test_normal(self):
        """Establish that the data about a project update retrieved from the
        project updates endpoint is provided.
        """
        with client.test_mode as t:
            t.register_json('/inventory_sources/1/', {
                'id': 1,
                'related': {'last_update': '/api/v1%s' % self.detail_uri},
            })
            t.register_json(self.detail_uri, {
                'elapsed': 1335024000.0,
                'extra': 'ignored',
                'failed': False,
                'status': 'successful',
            })
            result = self.res.status(1)
            self.assertEqual(result, {
                'elapsed': 1335024000.0,
                'failed': False,
                'status': 'successful',
            })
            self.assertEqual(len(t.requests), 2)

    def test_detailed(self):
        """Establish that a detailed request is sent back in the way
        that we expect.
        """
        with client.test_mode as t:
            t.register_json('/inventory_sources/1/', {
                'id': 1,
                'related': {'last_update': '/api/v1%s' % self.detail_uri},
            })
            t.register_json(self.detail_uri, {
                'elapsed': 1335024000.0,
                'extra': 'ignored',
                'failed': False,
                'status': 'successful',
            })
            result = self.res.status(1, detail=True)
            self.assertEqual(result, {
                'elapsed': 1335024000.0,
                'extra': 'ignored',
                'failed': False,
                'status': 'successful',
            })
            self.assertEqual(len(t.requests), 2)

    def test_currently_running_update(self):
        """Establish that if an update is currently running, that we see this
        and send back the appropriate status.
        """
        with client.test_mode as t:
            t.register_json('/inventory_sources/1/', {
                'id': 1,
                'related': {
                    'current_update': '/api/v1%s' % self.detail_uri,
                    'last_update': '/api/v1%s' %
                                   self.detail_uri.replace('42', '41'),
                },
            })
            t.register_json(self.detail_uri, {
                'elapsed': 1335024000.0,
                'extra': 'ignored',
                'failed': False,
                'status': 'running',
            })
            result = self.res.status(1)
            self.assertEqual(result, {
                'elapsed': 1335024000.0,
                'failed': False,
                'status': 'running',
            })
            self.assertEqual(len(t.requests), 2)

    def test_no_updates(self):
        """Establish that running `status` against a project with no updates
        raises the error we expect.
        """
        with client.test_mode as t:
            t.register_json('/inventory_sources/1/', {
                'id': 1,
                'related': {},
            })
            with self.assertRaises(exc.NotFound):
                self.res.status(1)
