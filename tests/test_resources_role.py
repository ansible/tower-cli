# Copyright 2016, Ansible by Red Hat
# Alan Rominger <arominge@redhat.com>
# Aaron Tan <sitan@redhat.com>
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

# used to test static methods
from tower_cli.resources.role import Resource as Role
from tower_cli.utils import exceptions as exc
from tower_cli.conf import settings

from tests.compat import unittest, mock
from copy import copy

example_role_data = {
    "id": 1, "type": "role", "url": "/api/v1/roles/1/",
    "related": {"users": "/api/v1/roles/1/users/",
                "teams": "/api/v1/roles/1/teams/"},
    "summary_fields": {},
    "name": "System Administrator",
    "description": "Can manage all aspects of the system"}


class RoleUnitTests(unittest.TestCase):
    """Test role internal helper functions."""

    def test_plurals(self):
        """English words changed from singular to plural"""
        self.assertEqual(Role.pluralize("inventory"), "inventories")
        self.assertEqual(Role.pluralize("job_template"), "job_templates")

    def test_obj_res_team(self):
        """Test that the input format can be correctly translated into the
        object & resource data structure for granting the resource role
        to the object.
        Do this for teams getting read permission on inventory here."""
        obj, obj_type, res, res_type = Role.obj_res(
            {"team": 3, "inventory": 5, "type": "read", "not_a_res": None,
             "credential": None, "project": None})
        self.assertEqual(obj, 3)
        self.assertEqual(obj_type, 'team')
        self.assertEqual(res, 5)
        self.assertEqual(res_type, 'inventory')

    def test_obj_res_missing_errors(self):
        """Testing obj_res method, ability to produce errors here."""
        with self.assertRaises(exc.UsageError):
            obj, obj_type, res, res_type = Role.obj_res(
                {"inventory": None, "credential": None})

    def test_obj_res_too_many_errors(self):
        """Testing obj_res method, ability to duplicate errors."""
        with self.assertRaises(exc.UsageError):
            obj, obj_type, res, res_type = Role.obj_res(
                {"inventory": 1, "target_team": 2, "user": 3, "team": 5})

    def test_populate_resource_columns(self):
        """Test function that fills in extra columns"""
        singleton_output = copy(example_role_data)
        Role.populate_resource_columns(singleton_output)
        self.assertIn('resource_name', singleton_output)
        # Case for non-singleton roles
        normal_output = copy(example_role_data)
        normal_output['summary_fields'] = {
            "resource_name": "Default",
            "resource_type": "organization",
            "resource_type_display_name": "Organization"}
        Role.populate_resource_columns(normal_output)
        self.assertIn('resource_name', normal_output)

    def test_data_endpoint_team_no_res(self):
        """Translation of input args to lookup args, using team"""
        kwargs = {'team': 2}
        data, endpoint = Role.data_endpoint(kwargs, ignore=[])
        self.assertEqual(endpoint, 'teams/2/roles/')
        self.assertNotIn('object_id', data)

    def test_data_endpoint_inventory_ignore(self):
        """Translation of input args to lookup args, ignoring inventory"""
        kwargs = {'user': 2, 'type': 'admin', 'inventory': 5}
        data, endpoint = Role.data_endpoint(kwargs, ignore=['res'])
        self.assertIn('members__in', data)
        self.assertEqual(endpoint, '/roles/')


class RoleMethodTests(unittest.TestCase):
    """Test role commands."""

    def setUp(self):
        self.res = tower_cli.get_resource('role')

    def test_removed_methods(self):
        """Test that None is returned from removed methods."""
        self.assertEqual(
            self.res.as_command().get_command(None, 'delete'), None)

    def test_configure_write_display(self):
        """Test that output configuration for writing to role works."""
        data = copy(example_role_data)
        kwargs = {'user': 2, 'inventory': 3, 'type': 'admin'}
        self.res.configure_display(data, kwargs, write=True)
        self.assertIn('user', data)

    def test_list_user(self):
        """Assure that super method is called with right parameters"""
        with mock.patch(
                'tower_cli.models.base.ResourceMethods.list') as mock_list:
            mock_list.return_value = {'results': [example_role_data]}
            self.res.list(user=1)
            mock_list.assert_called_once_with(members__in=1)

    def test_list_team(self):
        """Teams can not be passed as a parameter, check use of sublist"""
        with mock.patch(
                'tower_cli.models.base.ResourceMethods.list') as mock_list:
            mock_list.return_value = {'results': []}
            self.res.list(team=1, inventory=3, type='read')
            mock_list.assert_called_once_with(
                object_id=3, role_field='read_role')
            self.assertEqual(self.res.endpoint, 'teams/1/roles/')

    def test_list_resource(self):
        """Listing based on a resource the role applies to"""
        with mock.patch(
                'tower_cli.models.base.ResourceMethods.list') as mock_list:
            mock_list.return_value = {'results': []}
            self.res.list(inventory=3, type='read')
            mock_list.assert_called_once_with(role_field='read_role')
            self.assertEqual(self.res.endpoint, 'inventories/3/object_roles/')

    def test_get_user(self):
        """Assure that super method is called with right parameters"""
        with mock.patch(
                'tower_cli.models.base.ResourceMethods.read') as mock_read:
            mock_read.return_value = {'results': [copy(example_role_data)]}
            with settings.runtime_values(format='human'):
                self.res.get(user=1)
            mock_read.assert_called_once_with(
                fail_on_multiple_results=True, fail_on_no_results=True,
                members__in=1, pk=None)

    def test_get_user_json(self):
        """Test internal use with json format, no debug"""
        with mock.patch(
                'tower_cli.models.base.ResourceMethods.read') as mock_read:
            mock_read.return_value = {'results': [{
                'name': 'arole', 'summary_fields': {}}]}
            with settings.runtime_values(format='json'):
                self.res.get(user=1, include_debug_header=False)
            mock_read.assert_called_once_with(
                fail_on_multiple_results=True, fail_on_no_results=True,
                members__in=1, pk=None)

    def test_grant_user_role(self):
        """Assure that super method is called granting role"""
        with mock.patch(
                'tower_cli.resources.role.Resource.role_write') as mock_write:
            kwargs = dict(user=1, type='read', project=3)
            self.res.grant(**kwargs)
            mock_write.assert_called_once_with(fail_on_found=False, **kwargs)

    def test_revoke_user_role(self):
        """Assure that super method is called revoking role"""
        with mock.patch(
                'tower_cli.resources.role.Resource.role_write') as mock_write:
            kwargs = dict(user=1, type='read', project=3)
            self.res.revoke(**kwargs)
            mock_write.assert_called_once_with(fail_on_found=False,
                                               disassociate=True, **kwargs)

    def test_role_write_user_exists(self):
        """Simulate granting user permission where they already have it."""
        with mock.patch(
                'tower_cli.models.base.ResourceMethods.read') as mock_read:
            mock_read.return_value = {'results': [copy(example_role_data)],
                                      'count': 1}
            r = self.res.role_write(user=2, inventory=3, type='admin')
            self.assertEqual(r['user'], 2)

    def test_role_write_user_exists_FOF(self):
        """Simulate granting user permission where they already have it."""
        with mock.patch(
                'tower_cli.models.base.ResourceMethods.read') as mock_read:
            mock_read.return_value = {'results': [copy(example_role_data)],
                                      'count': 1}
            with mock.patch('tower_cli.api.Client.post'):
                with self.assertRaises(exc.NotFound):
                    self.res.role_write(user=2, inventory=3, type='admin',
                                        fail_on_found=True)

    def test_role_write_user_does_not_exist(self):
        """Simulate revoking user permission where they already lack it."""
        with mock.patch(
                'tower_cli.models.base.ResourceMethods.read') as mock_read:
            mock_read.return_value = {'results': [copy(example_role_data)],
                                      'count': 0}
            r = self.res.role_write(user=2, inventory=3, type='admin',
                                    disassociate=True)
            self.assertEqual(r['user'], 2)

    def test_role_grant_user(self):
        """Simulate granting user permission."""
        with mock.patch(
                'tower_cli.models.base.ResourceMethods.read') as mock_read:
            mock_read.return_value = {
                'results': [copy(example_role_data)], 'count': 0}
            with mock.patch('tower_cli.api.Client.post') as mock_post:
                self.res.role_write(user=2, inventory=3, type='admin')
                mock_post.assert_called_once_with(
                    'users/2/roles/', data={'id': 1})

    def test_role_revoke_user(self):
        """Simulate granting user permission."""
        with mock.patch(
                'tower_cli.models.base.ResourceMethods.read') as mock_read:
            mock_read.return_value = {
                'results': [copy(example_role_data)], 'count': 1}
            with mock.patch('tower_cli.api.Client.post') as mock_post:
                self.res.role_write(user=2, inventory=3, type='admin',
                                    disassociate=True)
                mock_post.assert_called_once_with(
                    'users/2/roles/', data={'id': 1, 'disassociate': True})
