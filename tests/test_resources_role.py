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

from tests.compat import unittest, mock


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
            {"team": 3, "inventory": 5, "type": "read", "not_a_res": None}
        )
        self.assertEqual(obj, 3)
        self.assertEqual(obj_type, 'team')
        self.assertEqual(res, 5)
        self.assertEqual(res_type, 'inventory')

    def test_obj_res_user(self):
        """Testing obj_res method, user on credential here."""
        obj, obj_type, res, res_type = Role.obj_res(
            {"user": 2, "inventory": None, "type": "read", "credential": 9}
        )
        self.assertEqual(obj, 2)
        self.assertEqual(obj_type, 'user')
        self.assertEqual(res, 9)
        self.assertEqual(res_type, 'credential')

    def test_obj_res_errors(self):
        """Testing obj_res method, ability to produce errors here."""
        with self.assertRaises(exc.UsageError):
            obj, obj_type, res, res_type = Role.obj_res(
                {"inventory": None, "credential": None}
            )


class RoleTests(unittest.TestCase):
    """Test role commands."""

    def setUp(self):
        self.res = tower_cli.get_resource('role')

    def test_removed_methods(self):
        """Test that None is returned from removed methods."""
        self.assertEqual(
            self.res.as_command().get_command(None, 'delete'), None)

    def test_list_user(self):
        """Assure that super method is called with right parameters"""
        with mock.patch(
                'tower_cli.models.base.ResourceMethods.list') as mock_list:
            mock_list.return_value = {'results': []}
            self.res.list(user=1)
            mock_list.assert_called_once_with(members__in=1)

    def test_list_team(self):
        """Teams can not be passed as a parameter, check use of sublist"""
        with mock.patch(
                'tower_cli.models.base.ResourceMethods.list') as mock_list:
            mock_list.return_value = {'results': []}
            self.res.list(team=1, inventory=3, type='read')
            mock_list.assert_called_once_with(
                content_id=3, role_field='read_role')
            self.assertEqual(self.res.endpoint, 'teams/1/roles/')

    def test_list_resource(self):
        """Listing based on a resource the role applies to"""
        with mock.patch(
                'tower_cli.models.base.ResourceMethods.list') as mock_list:
            mock_list.return_value = {'results': []}
            self.res.list(inventory=3, type='read')
            mock_list.assert_called_once_with(
                role_field='read_role')
            self.assertEqual(self.res.endpoint, 'inventories/3/object_roles/')

    def test_get_user(self):
        """Assure that super method is called with right parameters"""
        with mock.patch(
                'tower_cli.models.base.ResourceMethods.read') as mock_read:
            mock_read.return_value = {'results': [{
                'name': 'arole', 'summary_fields': {}}]}
            self.res.get(user=1)
            mock_read.assert_called_once_with(
                fail_on_multiple_results=True, fail_on_no_results=True,
                members__in=1, pk=None)
