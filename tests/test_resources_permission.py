# Copyright 2016, Red Hat
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
from tower_cli.utils import exceptions as exc

from tests.compat import unittest


def create_registrations(t):
    t.register_json('/users/3/permissions/', {'count': 0, 'results': [],
                    'next': None, 'previous': None}, method='GET')
    t.register_json('/users/3/permissions/', {'id': 4}, method='POST')


def existing_registrations(t):
    t.register_json('/users/3/permissions/', {'count': 1,
                    'results': [{'id': 4, 'name': 'bar'}],
                    'next': None, 'previous': None}, method='GET')
    t.register_json('/permissions/4/', {'id': 4}, method='GET')


class PermissionTests(unittest.TestCase):
    """A set of tests for checking that the permission feature works
    correctly.
    """
    def setUp(self):
        self.res = tower_cli.get_resource('permission')

    def test_create_default_permission_type(self):
        with client.test_mode as t:
            create_registrations(t)
            result = self.res.create(
                name='bar', user=3, inventory=9
            )
            self.assertEqual(t.requests[0].method, 'GET')
            self.assertDictContainsSubset({'id': 4}, result)

    def test_create_write_type(self):
        with client.test_mode as t:
            create_registrations(t)
            result = self.res.create(
                name='bar', user=3, inventory=9, permission_type='write'
            )
            self.assertEqual(t.requests[0].method, 'GET')
            self.assertDictContainsSubset({'id': 4}, result)

    def test_set_base_url_user(self):
        self.res.set_base_url(1, None)
        self.assertEqual(self.res.endpoint, '/users/1/permissions/')

    def test_set_base_url_team(self):
        self.res.set_base_url(None, 1)
        self.assertEqual(self.res.endpoint, '/teams/1/permissions/')

    def test_no_user_or_team(self):
        with self.assertRaises(exc.TowerCLIError):
            self.res.set_base_url(None, None)

    def test_delete_permission(self):
        with client.test_mode as t:
            existing_registrations(t)
            t.register_json('/permissions/4/', {}, method='DELETE')
            result = self.res.delete(name='bar', user=3)
            self.assertTrue(result['changed'])

    def test_modify_permission(self):
        with client.test_mode as t:
            existing_registrations(t)
            t.register_json('/permissions/4/', {'id': 4, 'name': 'bar'},
                            method='PATCH')
            result = self.res.modify(name='bar', user=3,
                                     permission_type='admin')
            self.assertTrue(result['changed'])

    def test_modify_permission_by_pk(self):
        with client.test_mode as t:
            existing_registrations(t)
            t.register_json('/permissions/4/', {'id': 4, 'name': 'bar'},
                            method='PATCH')
            result = self.res.modify(4, permission_type='admin')
            self.assertTrue(result['changed'])

    def test_list_permissions(self):
        with client.test_mode as t:
            existing_registrations(t)
            result = self.res.list(user=3)
            self.assertEqual(result['count'], 1)
