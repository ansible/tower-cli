# Copyright 2015, Red Hat, Inc.
# Alan Rominger <arominge@redhat.com>
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

from tests.compat import unittest, mock


class CredentialTests(unittest.TestCase):
    """A set of tests for ensuring that the credential resource's create
    command works in the way we expect.
    """
    def setUp(self):
        self.res = tower_cli.get_resource('credential')

    def test_create_without_special_fields(self):
        """Establish that a create without user, team, or credential works"""
        with mock.patch(
                'tower_cli.models.base.Resource.create') as mock_create:
            cred_res = tower_cli.get_resource('credential')
            cred_res.create(name="foobar")
            mock_create.assert_called_once_with(name="foobar")

    def test_create_with_special_fields_old(self):
        """Establish that creating with special fields passes through as-is
        if the API does not support this use mode."""
        with client.test_mode as t:
            t.register_json('/credentials/', {'actions': {'POST': {}}},
                            method='OPTIONS')
            with mock.patch(
                    'tower_cli.models.base.Resource.create') as mock_create:
                cred_res = tower_cli.get_resource('credential')
                cred_res.create(name="foobar", organization="Foo Ops")
                mock_create.assert_called_once_with(
                    name="foobar", organization="Foo Ops")

    def test_create_with_special_fields_new(self):
        """Establish that creating with special fields uses special no_lookup
        tool if given special fields and the API supports that use case."""
        with client.test_mode as t:
            t.register_json(
                '/credentials/', {'actions': {'POST': {
                    'organization': 'information'}}}, method='OPTIONS')
            with mock.patch(
                    'tower_cli.models.base.Resource.create') as mock_create:
                cred_res = tower_cli.get_resource('credential')
                cred_res.create(name="foobar", organization="Foo Ops")
                mock_create.assert_called_once_with(
                    name="foobar", organization="Foo Ops")
                self.assertTrue(cred_res.fields[2].no_lookup)

    def test_create_with_special_fields_new_functional(self):
        """Establish that the correct GET data is used with the new
        method for creating credentials."""
        with client.test_mode as t:
            t.register_json(
                '/credentials/', {'actions': {'POST': {
                    'organization': 'information'}}}, method='OPTIONS')
            t.register_json('/credentials/', {'count': 0, 'results': [],
                            'next': None, 'previous': None}, method='GET')
            t.register_json('/credentials/', {'count': 0, 'results': [],
                            'next': None, 'previous': None}, method='GET')
            t.register_json('/credentials/', {'id': 42}, method='POST')

            cred_res = tower_cli.get_resource('credential')
            cred_res.create(name="foobar", user=1, kind="ssh")
            self.assertTrue(cred_res.fields[2].no_lookup)
            self.assertTrue(cred_res.fields[3].no_lookup)

            # Verify request data is correct
            self.assertEqual(len(t.requests), 3)
            self.assertEqual(t.requests[0].method, 'OPTIONS')
            self.assertEqual(t.requests[1].method, 'GET')
            self.assertEqual(t.requests[2].method, 'POST')
            self.assertTrue('name=foobar' in t.requests[1].url)
            # Make sure special fields not used for GET
            self.assertTrue('user' not in t.requests[1].url)
            # Make sure special files are used in actual POST
            self.assertTrue('user' in t.requests[2].body)
