# -*- coding: utf-8 -*-

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

import json

import six

import tower_cli
from tower_cli.api import client
from tower_cli.utils import exceptions as exc
from tower_cli.utils.data_structures import OrderedDict

from tests.compat import unittest


class SettingTests(unittest.TestCase):
    """A set of tests to establish that the setting resource functions in the
    way that we expect.
    """
    def setUp(self):
        self.res = tower_cli.get_resource('setting')

    def test_create_method_is_disabled(self):
        """Establish that the delete method properly disabled."""
        self.assertEqual(self.res.as_command().get_command(None, 'create'),
                         None)

    def test_delete_method_is_disabled(self):
        """Establish that the create method properly disabled."""
        self.assertEqual(self.res.as_command().get_command(None, 'delete'),
                         None)

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
                [
                    {'id': 'FIRST', 'value': 123},
                    {'id': 'SECOND', 'value': 'foo'}
                ]
            )

    def test_list_all_by_category(self):
        """Establish that settings can be listed by category"""
        system_settings = OrderedDict({'FEATURE_ENABLED': True})
        auth_settings = OrderedDict({'SOME_API_KEY': 'ABC123'})
        with client.test_mode as t:
            t.register_json('/settings/system/', system_settings)
            t.register_json('/settings/authentication/', auth_settings)

            r = self.res.list(category='system')
            self.assertEqual(
                r['results'],
                [{'id': 'FEATURE_ENABLED', 'value': True}]
            )

            r = self.res.list(category='authentication')
            self.assertEqual(
                r['results'],
                [{'id': 'SOME_API_KEY', 'value': 'ABC123'}]
            )

    def test_list_invalid_category(self):
        """Establish that settings can only be listed by valid categories"""
        categories = {
            'results': [{
                'url': '/api/v1/settings/all/',
                'name': 'All',
                'slug': 'all'
            }, {
                'url': '/api/v1/settings/logging/',
                'name': 'Logging',
                'slug': 'logging'
            }]
        }
        with client.test_mode as t:
            t.register_json('/settings/', categories)
            t.register_json('/settings/authentication/', '', status_code=404)
            with self.assertRaises(exc.NotFound) as e:
                self.res.list(category='authentication')
            self.assertEqual(
                e.exception.message,
                ('authentication is not a valid category.  Choose from '
                 '[all, logging]')
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
        new_val = 456
        all_settings = OrderedDict({'FIRST': 123})
        patched = OrderedDict({'FIRST': new_val})
        with client.test_mode as t:
            t.register_json('/settings/all/', all_settings)
            t.register_json('/settings/all/', patched, method='PATCH')
            r = self.res.modify('FIRST', new_val)
            self.assertTrue(r['changed'])

            request = t.requests[0]
            self.assertEqual(request.method, 'GET')

            request = t.requests[1]
            self.assertEqual(request.method, 'PATCH')
            self.assertEqual(request.body, json.dumps({'FIRST': new_val}))

    def test_update_with_unicode(self):
        """Establish that a setting's value can updated with unicode"""
        new_val = six.u('Iñtërnâtiônàlizætiøn')
        all_settings = OrderedDict({'FIRST': 123})
        patched = OrderedDict({'FIRST': new_val})
        with client.test_mode as t:
            t.register_json('/settings/all/', all_settings)
            t.register_json('/settings/all/', patched, method='PATCH')
            r = self.res.modify('FIRST', new_val)
            self.assertTrue(r['changed'])

            request = t.requests[0]
            self.assertEqual(request.method, 'GET')

            request = t.requests[1]
            self.assertEqual(request.method, 'PATCH')
            self.assertEqual(request.body, json.dumps({'FIRST': new_val}))

    def test_idempotent_updates_ignored(self):
        """Don't PATCH a setting if the provided value didn't change"""
        all_settings = OrderedDict({'FIRST': 123})
        with client.test_mode as t:
            t.register_json('/settings/all/', all_settings)
            r = self.res.modify('FIRST', '123')
            self.assertFalse(r['changed'])

            self.assertEqual(len(t.requests), 1)
            request = t.requests[0]
            self.assertEqual(request.method, 'GET')

    def test_encrypted_updates_always_patch(self):
        """Always PATCH a setting if it's an encrypted one"""
        all_settings = OrderedDict({'SECRET': '$encrypted$'})
        patched = OrderedDict({'SECRET': '$encrypted$'})
        with client.test_mode as t:
            t.register_json('/settings/all/', all_settings)
            t.register_json('/settings/all/', patched, method='PATCH')
            r = self.res.modify('SECRET', 'SENSITIVE')
            self.assertTrue(r['changed'])

            self.assertEqual(len(t.requests), 2)
            request = t.requests[0]
            self.assertEqual(request.method, 'GET')

            request = t.requests[1]
            self.assertEqual(request.method, 'PATCH')
            self.assertEqual(request.body, json.dumps({'SECRET': 'SENSITIVE'}))

    def test_update_invalid_setting_name(self):
        """Establish that a setting must exist to be updated"""
        all_settings = OrderedDict({'FIRST': 123})
        with client.test_mode as t:
            t.register_json('/settings/all/', all_settings)
            t.register_json('/settings/all/', all_settings, method='PATCH')
            self.assertRaises(exc.NotFound, self.res.modify, 'MISSING', 456)
