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

import json
import time
from copy import copy

import click

from six.moves import StringIO

import tower_cli
from tower_cli.api import client
from tower_cli.utils import exceptions as exc

from tests.compat import unittest, mock


class UpdateTests(unittest.TestCase):
    """A set of tests for ensuring that the project resource's update command
    works in the way we expect.
    """
    def setUp(self):
        self.res = tower_cli.get_resource('project')

    def test_basic_update(self):
        """Establish that we are able to create a project update
        and return the changed status.
        """
        with client.test_mode as t:
            t.register_json('/projects/1/', {
                'id': 1,
                'name': 'frobnicate',
                'related': {'update': '/api/v1/projects/1/update/'},
            })
            t.register_json('/projects/1/update/', {'can_update': True},
                            method='GET')
            t.register_json('/projects/1/update/', {'project_update': 42},
                            method='POST')
            result = self.res.update(1)
            self.assertEqual(result, {'changed': True})

    def test_basic_update_with_monitor(self):
        """Establish that we are able to create a project update
        and shift to monitoring if requested.
        """
        with client.test_mode as t:
            t.register_json('/projects/1/', {
                'id': 1,
                'name': 'frobnicate',
                'related': {'update': '/api/v1/projects/1/update/'},
            })
            t.register_json('/projects/1/update/', {'can_update': True},
                            method='GET')
            t.register_json('/projects/1/update/', {'project_update': 42},
                            method='POST')
            with mock.patch.object(type(self.res), 'monitor') as monitor:
                result = self.res.update(1, monitor=True)
                monitor.assert_called_once_with(1, timeout=None)

    def test_cannot_update(self):
        """Establish that attempting to update a non-updatable project
        errors out as expected.
        """
        with client.test_mode as t:
            t.register_json('/projects/1/', {
                'id': 1,
                'name': 'frobnicate',
                'related': {'update': '/api/v1/projects/1/update/'},
            })
            t.register_json('/projects/1/update/', {'can_update': False},
                            method='GET')
            with self.assertRaises(exc.CannotStartJob):
                result = self.res.update(1)


class StatusTests(unittest.TestCase):
    """A set of tests to establish that the project status command works in
    the way that we expect.
    """
    def setUp(self):
        self.res = tower_cli.get_resource('project')

    def test_normal(self):
        """Establish that the data about a project update retrieved from the
        project updates endpoint is provided.
        """
        with client.test_mode as t:
            t.register_json('/projects/1/', {
                'id': 1,
                'related': {'last_update':
                            '/api/v1/projects/1/project_updates/42/'},
            })
            t.register_json('/projects/1/project_updates/42/', {
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
            t.register_json('/projects/1/', {
                'id': 1,
                'related': {'last_update':
                            '/api/v1/projects/1/project_updates/42/'},
            })
            t.register_json('/projects/1/project_updates/42/', {
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
            t.register_json('/projects/1/', {
                'id': 1,
                'related': {
                    'current_update': '/api/v1/projects/1/project_updates/42/',
                    'last_update': '/api/v1/projects/1/project_updates/41/',
                },
            })
            t.register_json('/projects/1/project_updates/42/', {
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
            t.register_json('/projects/1/', {
                'id': 1,
                'related': {},
            })
            with self.assertRaises(exc.NotFound):
                result = self.res.status(1)
