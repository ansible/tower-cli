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

import tower_cli
from tower_cli.api import client
from tower_cli.utils import exceptions as exc

from tests.compat import unittest, mock


class InventorySourceTests(unittest.TestCase):
    """A set of tests to establish that the inventory source resource works
    in the way that we expect.
    """
    def setUp(self):
        self.isr = tower_cli.get_resource('inventory_source')

    def test_cannot_sync(self):
        """Establish that if we attempt to sync an inventory source that
        cannot be updated, that we raise BadRequest.
        """
        with client.test_mode as t:
            t.register_json('/inventory_sources/1/update/',
                            {'can_update': False}, method='GET')
            with self.assertRaises(exc.BadRequest):
                self.isr.sync(1)

    def test_sync(self):
        """Establish that if we are able to update an inventory source,
        that the sync command does so.
        """
        with client.test_mode as t:
            t.register_json('/inventory_sources/1/update/',
                            {'can_update': True}, method='GET')
            t.register_json('/inventory_sources/1/update/',
                            {}, method='POST')
            answer = self.isr.sync(1)
            self.assertEqual(answer['status'], 'ok')
