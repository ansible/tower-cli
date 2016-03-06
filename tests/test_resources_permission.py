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

from tests.compat import unittest, mock

def common_registrations(t):
    t.register_json('/users/3/permissions/', {'count': 0, 'results': [],
                    'next': None, 'previous': None}, method='GET')
    t.register_json('/users/3/permissions/', {'id': 4}, method='POST')


class PermissionTests(unittest.TestCase):
    """A set of tests for checking that the permission feature works
    correctly.
    """
    def setUp(self):
        self.res = tower_cli.get_resource('permission')

    def test_create_default_permission_type(self):
        with client.test_mode as t:
            common_registrations(t)
            result = self.res.create(
                name='bar', user=3, inventory=9
            )
            self.assertEqual(t.requests[0].method, 'GET')
            self.assertDictContainsSubset({'id': 4}, result)
            
    def test_create_write_type(self):
        with client.test_mode as t:
            common_registrations(t)
            result = self.res.create(
                name='bar', user=3, inventory=9, permission_type='write'
            )
            self.assertEqual(t.requests[0].method, 'GET')
            self.assertDictContainsSubset({'id': 4}, result)
