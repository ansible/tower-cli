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
            super_create.assert_called_once_with(
                fail_on_found=False, force_on_exists=False,
                name='Foo', inventory=1)
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
                fail_on_found=False, force_on_exists=False,
                name='Foo', inventory=1)
            self.assertFalse(answer['changed'])

    def test_create_change_but_no_isource_request_needed(self):
        """Establish that if we make a new group but don't have any interesting
        inventory source arguments, that the group creation stands with no
        further requests.
        """
        with client.test_mode as t:
            t.register_json('/groups/?name=Foo', {
                'count': 0,
                'next': None,
                'previous': None,
                'results': [],
            }, method='GET')
            t.register_json('/groups/', {
                'id': 1,
                'name': 'Foo',
                'inventory': 1,
            }, method='POST')
            answer = self.gr.create(name='Foo', inventory=1)
            self.assertEqual(len(t.requests), 2)
        self.assertTrue(answer['changed'])

    def test_create_with_manual(self):
        """Try to change group to manual, find that it already is.
        """
        with client.test_mode as t:
            t.register_json('/groups/?name=Foo', {
                'count': 0,
                'next': None,
                'previous': None,
                'results': [],
            }, method='GET')
            t.register_json('/groups/', {
                'id': 1,
                'name': 'Foo',
                'inventory': 1,
            }, method='POST')
            answer = self.gr.create(name='Foo', inventory=1, source="manual")
            self.assertEqual(len(t.requests), 2)
        self.assertTrue(answer['changed'])

    def test_create_change_with_isource_modify(self):
        """Establish that if we make a new group and provide inventory source
        arguments, that a modify request is made for the inventory source.
        """
        with client.test_mode as t:
            t.register_json('/groups/?name=Foo', {
                'count': 0, 'results': [],
                'next': None, 'previous': None,
            }, method='GET')
            t.register_json('/groups/', {
                'id': 1, 'inventory': 1, 'name': 'Foo',
                'related': {'inventory_source': '/inventory_sources/42/'},
            }, method='POST')
            t.register_json('/inventory_sources/42/', {
                'id': 42, 'source': 'manual', 'credential': None,
            }, method='GET')
            t.register_json('/inventory_sources/42/', {
                'id': 42,
                'source': 'rax',
                'credential': None,
            }, method='PATCH')
            answer = self.gr.create(name='Foo', inventory=1, source='rax')
            self.assertEqual(len(t.requests), 4)
        self.assertTrue(answer['changed'])

    def test_create_FOE_with_isource_modify(self):
        """Establish that if we create a group, setting force_on_exists,
        and both the group and inventory_source are unchanged, that
        is correctly proceeds and echos that there was no change.
        """
        Foo_data = {'id': 1, 'name': 'Foo', 'inventory': 1,
                    'related': {'inventory_source': '/inventory_sources/42/'}}
        with client.test_mode as t:
            t.register_json('/groups/?name=Foo', {
                'count': 1, 'results': [Foo_data],
                'next': None, 'previous': None,
            }, method='GET')
            t.register_json('/inventory_sources/42/', {
                'id': 42, 'source': 'rax', 'credential': None,
            }, method='GET')
            answer = self.gr.create(name='Foo', inventory=1, source='rax',
                                    force_on_exists=True)
            self.assertEqual(len(t.requests), 2)
        self.assertFalse(answer['changed'])

    def test_modify_no_change(self):
        """Establish that if we attempt to modify a group and the group itself
        exists, that we do not attempt to hit the inventory source at all.
        """
        with mock.patch.object(models.Resource, 'modify') as super_modify:
            super_modify.return_value = {'changed': False}
            with client.test_mode as t:
                self.gr.modify(42, description='rax')
                self.assertEqual(len(t.requests), 0)
            super_modify.assert_called_once_with(
                pk=42, create_on_missing=False, description='rax')

    def test_modify_with_source_attr_change(self):
        """Establish that if we attempt to modify a field in a group's
        inventory_source, that the inventory source module is sent the
        modification command.
        """
        isrc = tower_cli.get_resource('inventory_source')
        with mock.patch.object(type(isrc), 'write') as isrc_modify:
            isrc_modify.return_value = {'changed': True}
            with client.test_mode as t:
                t.register_json('/groups/1/', {
                    'id': 1, 'name': 'foo', 'inventory': 1,
                    'related': {'inventory_source': '/inventory_sources/42/'},
                }, method='GET')
                r = self.gr.modify(1, name='foo', source='rax')
                self.assertEqual(len(t.requests), 1)
                # make sure that the module says it was changed
                self.assertEqual(r['changed'], True)
            isrc_modify.assert_called_once_with(
                pk=42, source='rax', force_on_exists=True,
            )

    def test_modify_with_group_attr_change(self):
        """ Test than when the group description is changed, we hit the
        endpoint for the group and not the inventory_source. """
        isrc = tower_cli.get_resource('inventory_source')
        with mock.patch.object(type(isrc), 'write') as isrc_modify:
            isrc_modify.return_value = {'changed': False}
            with client.test_mode as t:
                t.register_json('/groups/1/', {
                    'id': 1, 'name': 'foo', 'inventory': 1,
                    'related': {'inventory_source': '/inventory_sources/42/'},
                }, method='GET')
                t.register_json('/groups/1/', {
                    'id': 1, 'changed': True,
                    'related': {'inventory_source': '/inventory_sources/42/'},
                }, method='PATCH')
                r = self.gr.modify(
                    1, name='foo', description='rax servers', source='rax')
                self.assertEqual(len(t.requests), 2)
                # make sure that the module says it was changed
                self.assertEqual(r['changed'], True)

    def test_modify_with_change_manual(self):
        """Establish that if we modify a group, changing its source to
        manual, then the inventory_source is called with empty string.
        """
        isrc = tower_cli.get_resource('inventory_source')
        with mock.patch.object(type(isrc), 'write') as isrc_modify:
            with client.test_mode as t:
                t.register_json('/groups/1/', {
                    'id': 1, 'name': 'foo', 'inventory': 1,
                    'related': {'inventory_source': '/inventory_sources/42/'},
                }, method='GET')
                self.gr.modify(1, name='foo', source='manual')
                self.assertEqual(len(t.requests), 1)
            isrc_modify.assert_called_once_with(
                pk=42, source='', force_on_exists=True,
            )

    def test_sync(self):
        """Establish that the sync method correctly forwards to the
        inventory source method, after getting the inventory source ID.
        """
        isrc = tower_cli.get_resource('inventory_source')
        with mock.patch.object(type(isrc), 'update') as isrc_sync:
            with client.test_mode as t:
                t.register_json('/groups/1/', {
                    'id': 1, 'name': 'foo', 'inventory': 1,
                    'related': {'inventory_source': '/inventory_sources/42/'},
                }, method='GET')
                self.gr.sync(1)
                self.assertIn((42,), isrc_sync.call_args)
                self.assertEqual(len(t.requests), 1)

    def test_set_child_endpoint_id(self):
        """Test that we can change the endpoint to list children of another
        group - given the id of parent.
        """
        with client.test_mode as t:
            t.register_json('/groups/1/', {
                'id': 1, 'inventory': 1, 'name': 'Foo',
            }, method='GET')
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

    def test_create_no_inventory_error(self):
        """Establish that error is thrown when no group/inventory given."""
        with self.assertRaises(exc.UsageError):
            self.gr.create(1)

    def test_list_under_parent(self):
        """Establish that listing with a parent specified works."""
        with mock.patch(
                'tower_cli.models.base.ResourceMethods.list') as mock_list:
            with mock.patch(
                    'tower_cli.resources.group.Resource.lookup_with_inventory'
                    ):
                self.gr.list(parent="foo_group")
                mock_list.assert_called_once_with()

    def test_associate(self):
        """Establish that associate commands work."""
        with mock.patch(
                'tower_cli.models.base.ResourceMethods._assoc') as mock_assoc:
            with mock.patch(
                    'tower_cli.resources.group.Resource.lookup_with_inventory'
                    ) as mock_lookup:
                mock_lookup.return_value = {'id': 1}
                self.gr.associate(group=1, parent=2)
                mock_assoc.assert_called_once_with('children', 1, 1)

    def test_disassociate(self):
        """Establish that associate commands work."""
        with mock.patch(
                'tower_cli.models.base.ResourceMethods._disassoc'
                ) as mock_assoc:
            with mock.patch(
                    'tower_cli.resources.group.Resource.lookup_with_inventory'
                    ) as mock_lookup:
                mock_lookup.return_value = {'id': 1}
                self.gr.disassociate(group=1, parent=2)
                mock_assoc.assert_called_once_with('children', 1, 1)
