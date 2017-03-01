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

from collections import OrderedDict
import json

import tower_cli
from tower_cli.api import client
from tower_cli.utils import exceptions as exc

from tests.compat import unittest


class SettingTests(unittest.TestCase):
    """A set of tests to establish that the setting resource functions in the
    way that we expect.
    """
    def setUp(self):
        self.res = tower_cli.get_resource('setting')

    def test_create_method_is_disabled(self):
        """Establish that delete method properly disabled."""
        self.assertEqual(self.res.as_command().get_command(None, 'create'), None)

    def test_delete_method_is_disabled(self):
        """Establish that create method properly disabled."""
        self.assertEqual(self.res.as_command().get_command(None, 'delete'), None)

    def test_list_all(self):
        """Establish that all settings can be listed"""
        all_settings = OrderedDict({
            'FIRST': 123,
            'SECOND': 'foo'
        })
        with client.test_mode as t:
            t.register_json('/settings/all/', all_settings)
            r = self.res.list()
            self.assertEqual(
                sorted(r['results'], key=lambda k: k['id']),
                [{'id':'FIRST', 'value':123}, {'id':'SECOND', 'value':'foo'}]
            )

    def test_get(self):
        """Establish that individual settings can be retrieved"""
        all_settings = OrderedDict({'FIRST': 123})
        with client.test_mode as t:
            t.register_json('/settings/all/', all_settings)
            r = self.res.get('FIRST')
            self.assertEqual(r, {'id': 'FIRST', 'value': 123})

    def test_get_invalid(self):
        """Establish that invalid setting names throw an error"""
        all_settings = OrderedDict({'FIRST': 123})
        with client.test_mode as t:
            t.register_json('/settings/all/', all_settings)
            self.assertRaises(exc.NotFound, self.res.get, 'MISSING')

    def test_update(self):
        """Establish that a setting's value can updated"""
        all_settings = OrderedDict({'FIRST': 123})
        with client.test_mode as t:
            t.register_json('/settings/all/', all_settings)
            t.register_json('/settings/all/', all_settings, method='PATCH')
            r = self.res.modify('FIRST', value=456)

            request = t.requests[0]
            self.assertEqual(request.method, 'GET')

            request = t.requests[1]
            self.assertEqual(request.method, 'PATCH')
            self.assertEqual(request.body, json.dumps({'FIRST': 456}))

    def test_update_invalid_setting_name(self):
        """Establish that a setting must exist to be updated"""
        all_settings = OrderedDict({'FIRST': 123})
        with client.test_mode as t:
            t.register_json('/settings/all/', all_settings)
            t.register_json('/settings/all/', all_settings, method='PATCH')
            self.assertRaises(exc.NotFound, self.res.modify, 'MISSING', value=456)
