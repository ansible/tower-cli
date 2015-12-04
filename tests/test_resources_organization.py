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

import json

import tower_cli
from tower_cli.api import client

from tests.compat import unittest


class OrganizationTests(unittest.TestCase):
    """Establish that the organization resource methods work in the way
    that we expect.
    """
    def setUp(self):
        self.org_resource = tower_cli.get_resource('organization')

    def test_associate(self):
        """Establish that the associate method makes the HTTP requests
        that we expect.
        """
        with client.test_mode as t:
            t.register_json('/organizations/42/users/?id=84',
                            {'count': 0, 'results': []})
            t.register_json('/organizations/42/users/', {}, method='POST')
            self.org_resource.associate(42, 84)
            self.assertEqual(t.requests[1].body,
                             json.dumps({'associate': True, 'id': 84}))

    def test_associate_admin(self):
        """Same associate test, but for creating an admin"""
        with client.test_mode as t:
            t.register_json('/organizations/42/admins/?id=84',
                            {'count': 0, 'results': []})
            t.register_json('/organizations/42/admins/', {}, method='POST')
            self.org_resource.associate_admin(42, 84)
            self.assertEqual(t.requests[1].body,
                             json.dumps({'associate': True, 'id': 84}))

    def test_disassociate(self):
        """Establish that the associate method makes the HTTP requests
        that we expect.
        """
        with client.test_mode as t:
            t.register_json('/organizations/42/users/?id=84',
                            {'count': 1, 'results': [{'id': 84}],
                             'next': None, 'previous': None})
            t.register_json('/organizations/42/users/', {}, method='POST')
            self.org_resource.disassociate(42, 84)
            self.assertEqual(t.requests[1].body,
                             json.dumps({'disassociate': True, 'id': 84}))

    def test_disassociate_admin(self):
        """Same disassociate test, but for creating an admin"""
        with client.test_mode as t:
            t.register_json('/organizations/42/admins/?id=84',
                            {'count': 1, 'results': [{'id': 84}],
                             'next': None, 'previous': None})
            t.register_json('/organizations/42/admins/', {}, method='POST')
            self.org_resource.disassociate_admin(42, 84)
            self.assertEqual(t.requests[1].body,
                             json.dumps({'disassociate': True, 'id': 84}))

    def test_project_associate(self):
        """Test request for associating project with organization.
        """
        with client.test_mode as t:
            t.register_json('/organizations/42/projects/?id=84',
                            {'count': 0, 'results': []})
            t.register_json('/organizations/42/projects/', {}, method='POST')
            self.org_resource.associate_project(42, 84)
            self.assertEqual(t.requests[1].body,
                             json.dumps({'associate': True, 'id': 84}))

    def test_project_disassociate(self):
        """Test request for disassociating project with organization.
        """
        with client.test_mode as t:
            t.register_json('/organizations/42/projects/?id=84',
                            {'count': 1, 'results': [{'id': 84}],
                             'next': None, 'previous': None})
            t.register_json('/organizations/42/projects/', {}, method='POST')
            self.org_resource.disassociate_project(42, 84)
            self.assertEqual(t.requests[1].body,
                             json.dumps({'disassociate': True, 'id': 84}))
