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

import tower_cli
from tower_cli import models
from tower_cli.api import client
from tower_cli.utils import exceptions as exc

from tests.compat import unittest, mock


class GroupTests(unittest.TestCase):
    """A set of tests to establish that the group resource functions in the
    way that we expect.
    """
    def setUp(self):
        self.gr = tower_cli.get_resource('group')

    def test_root_and_no_inventory(self):
        """Establish that if we try to get root groups without specifying
        an inventory, that we get a usage error.
        """
        with self.assertRaises(exc.UsageError):
            self.gr.list(root=True, inventory=None)

    def test_root(self):
        """Establish that getting root groups from the Tower API works in
        the way that we expect.
        """
        with client.test_mode as t:
            t.register_json('/inventories/1/root_groups/', {
                'count': 2,
                'results': [
                    {'id': 1, 'name': 'Foo', 'inventory': 1},
                    {'id': 2, 'name': 'Bar', 'inventory': 2},
                ],
                'next': None,
                'previous': None,
            })
            result = self.gr.list(root=True, inventory=1)
            self.assertEqual(result['results'], [
                {'id': 1, 'name': 'Foo', 'inventory': 1},
                {'id': 2, 'name': 'Bar', 'inventory': 2},
            ])

    def test_normal_situation(self):
        """Test that anything not covered by the subclass implementation
        simply calls the superclass implementation.
        """
        with mock.patch.object(models.Resource, 'list') as super_list:
            self.gr.list(root=False)
            super_list.assert_called_once_with()
