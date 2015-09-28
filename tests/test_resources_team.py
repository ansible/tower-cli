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


class TeamTests(unittest.TestCase):
    """Establish that the team resource methods work in the way
    that we expect.
    """
    def setUp(self):
        self.team_resource = tower_cli.get_resource('team')

    def test_associate(self):
        """Establish that the associate method makes the HTTP requests
        that we expect.
        """
        with client.test_mode as t:
            t.register_json('/teams/42/users/?id=84',
                            {'count': 0, 'results': []})
            t.register_json('/teams/42/users/', {}, method='POST')
            self.team_resource.associate(42, 84)
            self.assertEqual(t.requests[1].body,
                             json.dumps({'associate': True, 'id': 84}))

    def test_disassociate(self):
        """Establish that the associate method makes the HTTP requests
        that we expect.
        """
        with client.test_mode as t:
            t.register_json('/teams/42/users/?id=84',
                            {'count': 1, 'results': [{'id': 84}],
                             'next': None, 'previous': None})
            t.register_json('/teams/42/users/', {}, method='POST')
            self.team_resource.disassociate(42, 84)
            self.assertEqual(t.requests[1].body,
                             json.dumps({'disassociate': True, 'id': 84}))
