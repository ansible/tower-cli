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
from tower_cli import models, exceptions as exc
from tower_cli.api import client

from tests.compat import unittest, mock


class GroupTests(unittest.TestCase):
    """A set of tests to establish that the group resource functions in the
    way that we expect.
    """
    def setUp(self):
        self.gr = tower_cli.get_resource('group')

    def test_set_child_endpoint_id(self):
        """Test that we can change the endpoint to list children of another
        group - given the id of parent.
        """
        with client.test_mode as t:
            t.register_json('/groups/1/', {'id': 1, 'inventory': 1, 'name': 'Foo'}, method='GET')
            self.gr.set_child_endpoint(1)
            self.assertEqual(self.gr.endpoint, '/groups/1/children/')

    def test_set_child_endpoint_name(self):
        """Test that we can change the endpoint to list children of another
        group - given the name of parent.
        """
        with client.test_mode as t:
            t.register_json('/groups/?name=Foo', {
                'count': 1, 'results': [{
                    'id': 1, 'inventory': 1, 'name': 'Foo',
                }],
                'next': None, 'previous': None,
            }, method='GET')
            self.gr.set_child_endpoint("Foo")
            self.assertEqual(self.gr.endpoint, '/groups/1/children/')

    def test_create_no_change(self):
        """Establish that if we try to create a group that already exists,
        that we return the standard changed: false.
        """
        with mock.patch.object(models.Resource, 'create') as super_create:
            super_create.return_value = {'changed': False, 'id': 1}
            with client.test_mode as t:
                answer = self.gr.create(name='Foo', inventory=1)
                self.assertEqual(len(t.requests), 0)
            # This also establishes that the "credential" argument above
            # was dropped at the superclass method (as it should be).
            super_create.assert_called_once_with(fail_on_found=False, force_on_exists=False, name='Foo', inventory=1)
            self.assertFalse(answer['changed'])

    def test_create_as_child(self):
        """Establish that if we start the creation process of a child group
        """
        with mock.patch.object(models.Resource, 'create') as super_create:
            super_create.return_value = {'changed': False, 'id': 1}
            with mock.patch.object(models.Resource, 'get') as super_get:
                super_get.return_value = {'id': 2, 'inventory': 1}
                with client.test_mode as t:
                    answer = self.gr.create(name='Foo', parent=2)
                    self.assertEqual(len(t.requests), 0)
                super_get.assert_called_once_with(2)
            super_create.assert_called_once_with(
                fail_on_found=False, force_on_exists=False, name='Foo', inventory=1, parent=2
            )
            self.assertFalse(answer['changed'])

    def test_create_no_inventory_error(self):
        """Establish that error is thrown when no group/inventory given."""
        with self.assertRaises(exc.UsageError):
            self.gr.create(1)

    def test_root_and_no_inventory(self):
        """Establish that if we try to get root groups without specifying
        an inventory, that we get a usage error.
        """
        with self.assertRaises(exc.UsageError):
            self.gr.list(root=True, inventory=None)

    def test_list_root(self):
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

    def test_list_normal_situation(self):
        """Test that anything not covered by the subclass implementation
        simply calls the superclass implementation.
        """
        with mock.patch.object(models.Resource, 'list') as super_list:
            self.gr.list(root=False)
            super_list.assert_called_once_with()

    def test_list_under_parent(self):
        """Establish that listing with a parent specified works."""
        with mock.patch('tower_cli.models.base.BaseResource.list') as mock_list:
            with mock.patch('tower_cli.resources.group.Resource.lookup_with_inventory'):
                self.gr.list(parent="foo_group")
                mock_list.assert_called_once_with()

    def test_associate(self):
        """Establish that associate commands work."""
        with mock.patch('tower_cli.models.base.BaseResource._assoc') as mock_assoc:
            with mock.patch('tower_cli.resources.group.Resource.lookup_with_inventory') as mock_lookup:
                mock_lookup.return_value = {'id': 1}
                self.gr.associate(group=1, parent=2)
                mock_assoc.assert_called_once_with('children', 1, 1)

    def test_disassociate(self):
        """Establish that associate commands work."""
        with mock.patch('tower_cli.models.base.BaseResource._disassoc') as mock_assoc:
            with mock.patch('tower_cli.resources.group.Resource.lookup_with_inventory') as mock_lookup:
                mock_lookup.return_value = {'id': 1}
                self.gr.disassociate(group=1, parent=2)
                mock_assoc.assert_called_once_with('children', 1, 1)
