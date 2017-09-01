# Copyright 2017, Ansible by Red Hat
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

from tests.compat import unittest


class InventoryTests(unittest.TestCase):
    def setUp(self):
        self.inv_resource = tower_cli.get_resource('inventory')

    def test_batch_update(self):
        with client.test_mode as t:
            t.register_json('/inventories/42/', {'id': 42})
            t.register_json('/inventories/42/update_inventory_sources/', ['foo', 'bar'], method='POST')
            self.assertEqual(self.inv_resource.batch_update(pk=42), ['foo', 'bar'])
