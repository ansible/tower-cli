# Copyright 2016, Ansible by RedHat.
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
from tower_cli.api import client
from tower_cli.utils import exceptions as exc

from tests.compat import unittest

import json
import copy


class NotificationTemplateTests(unittest.TestCase):
    """A set of tests for commands operating on the notification template
    """
    def setUp(self):
        self.res = tower_cli.get_resource('notification_template')
        self.endpoint = '/notification_templates/'

    def test_create_in_isolation(self):
        """Establish that we can create a notification template in isolation.
        """
        post_body = """
        {"name": "foo", "notification_type": "slack",
        "notification_configuration": {"token": "hey", "channels": ["a", "b"]},
        "description": "bar"}
        """
        with client.test_mode as t:
            t.register_json(self.endpoint+'?name=foo',
                            {'count': 0, 'results': []})
            t.register_json(self.endpoint, {'id': 18}, method='POST')
            self.res.create(name='foo', description='bar',
                            notification_type='slack', channels=('a', 'b'),
                            token='hey')
            self.assertEqual(json.loads(t.requests[1].body),
                             json.loads(post_body))

    def test_create_under_jt(self):
        """Establish that we can create a notification template under an
        existing job template.
        """
        post_body = """
        {"notification_type": "slack", "description": "bar",
        "notification_configuration": {"token": "hey", "channels": ["a", "b"]},
        "name": "foo"}
        """
        with client.test_mode as t:
            t.register_json('/job_templates/5/', {'id': 5})
            t.register_json(self.endpoint, {'count': 0, 'results': []},
                            notification_type='slack', description='bar',
                            name='foo')
            t.register_json('/job_templates/5/notification_templates_any/'
                            '?name=foo', {'count': 0, 'results': []})
            t.register_json('/job_templates/5/notification_templates_any/',
                            {'id': 16}, method='POST')
            self.res.create(name='foo', description='bar',
                            notification_type='slack', channels=('a', 'b'),
                            token='hey', job_template=5)
            self.assertEqual(json.loads(t.requests[3].body),
                             json.loads(post_body))

    def test_create_without_necessary_config_option(self):
        """Establish that creating a notification template without necessary
        notification configuration options will trigger exception.
        """
        with client.test_mode as t:
            t.register_json('/job_templates/5/', {'id': 5})
            t.register_json(self.endpoint, {'count': 0, 'results': []},
                            notification_type='slack', description='bar',
                            name='foo')
            with self.assertRaises(exc.TowerCLIError) as cm:
                self.res.create(name='foo', description='bar',
                                notification_type='slack', channels=('a', 'b'),
                                job_template=5)
            self.assertEqual(cm.exception.message,
                             'Required config field token not provided.')

    def test_delete(self):
        """Establish that we can delete an existing notification template.
        """
        with client.test_mode as t:
            t.register_json(self.endpoint + '?name=foo',
                            {'count': 1, 'results': [{'id': 13}]})
            t.register_json(self.endpoint + '13/', '', method='DELETE')
            result = self.res.delete(name='foo')
            self.assertTrue(result['changed'])

    def test_get(self):
        """Establish that we can get exactly one notification template.
        """
        with client.test_mode as t:
            t.register_json(self.endpoint + '?name=foo',
                            {'count': 1, 'results': [{'id': 15}]})
            result = self.res.get(name='foo')
            self.assertEqual(result['id'], 15)

    def test_list(self):
        """Establish that we can get a list of notification templates under
        certain criteria.
        """
        with client.test_mode as t:
            t.register_json(self.endpoint,
                            {'count': 1, 'results': [{'id': 9}],
                             'previous': None, 'next': None},
                            notification_type='irc', page='1')
            result = self.res.list(notification_type='irc', page=1)
            self.assertEqual(result['count'], 1)

    def test_config_fields_disabled_during_read(self):
        """Establish that configuration-related fields are not used for
        searching.
        """
        with client.test_mode as t:
            t.register_json(self.endpoint,
                            {'count': 1, 'results': [{'id': 15}]})
            self.res.get(channels=('a', 'b'), name='foo')
            self.assertTrue(t.requests[0].url.endswith('?name=foo'))

    def test_modify(self):
        """Establish that we can modify an existing notification,
        including primary fields and configuration-related fields.
        """
        nt = {
            'id': 17,
            'name': 'foo',
            'notification_type': 'slack',
            'notification_configuration': {
                'channels': ['a', 'b'],
                'token': 'hello'
            },
            'description': 'foo'
        }
        res = copy.deepcopy(nt)
        res['description'] = 'bar'

        r1 = """
        {"description": "bar"}
        """
        r3 = """
        {"description": "bar", "notification_configuration":
        {"token": "hi", "channels": ["a", "b"]}, "notification_type": "slack"}
        """

        with client.test_mode as t:
            t.register_json(self.endpoint + '17/', nt)
            t.register_json(self.endpoint + '17/', res, method='PATCH')
            self.res.modify(pk=17, description='bar', token='hi')
            self.assertEqual(json.loads(t.requests[1].body), json.loads(r1))
            self.assertEqual(json.loads(t.requests[3].body), json.loads(r3))

    def test_modify_with_notification_type_altered(self):
        """Establish that modifying an existing notification template to a new
        notification type must provide all related configuration fields also.
        """
        nt = {
            'id': 17,
            'name': 'foo',
            'notification_type': 'slack',
            'notification_configuration': {
                'channels': ['a', 'b'],
                'token': 'hello'
            },
            'description': 'bar'
        }

        with client.test_mode as t:
            t.register_json(self.endpoint + '17/', nt)
            with self.assertRaises(exc.TowerCLIError) as cm:
                self.res.modify(pk=17, description='bar',
                                notification_type='email', token='hi')
            self.assertEqual(cm.exception.message,
                             'Required config field username not provided.')

    def test_notification_configuration_ignore_configuration_options(self):
        """Establish that --notification-configuration option would ignore
        any configuration-related options.
        """
        nc = """
        {
            "channels": [
                "ho",
                "ha",
                "yoho"
            ],
            "token": "jingobells"
        }
        """
        with client.test_mode as t:
            t.register_json(self.endpoint, {'count': 0, 'results': []},
                            name='hey')
            t.register_json(self.endpoint, {'id': 19}, method='POST')
            self.res.create(name='hey', notification_type='slack',
                            notification_configuration=nc, username='a',
                            sender='b')
            self.assertEqual(json.loads(t.requests[1].body)
                             ['notification_configuration'], json.loads(nc))

    def test_incorrect_json_format(self):
        """Establish that incorrect json format would trigger exception.
        """
        nc = """
        {
            "channels": [
                "ho",
                "ha",
                "yoho"
            ],
            "token": "jingobells"
        """
        with self.assertRaises(exc.TowerCLIError) as cm:
            self.res.create(name='hey', notification_type='slack',
                            notification_configuration=nc)
        self.assertEqual(cm.exception.message,
                         'Provided json file format invalid. Please recheck.')

    def test_encrypted_fields_must_be_given(self):
        """Establish that encrypted configuration fields must be provided
        even in modification.
        """
        nt = {
            'id': 17,
            'name': 'foo',
            'notification_type': 'slack',
            'notification_configuration': {
                'channels': ['a', 'b'],
                'token': '$encrypted$'
            },
            'description': ''
        }
        with client.test_mode as t:
            t.register_json(self.endpoint + '12/', nt)
            with self.assertRaises(exc.TowerCLIError) as cm:
                self.res.modify(pk=12, channels=('1',))
            self.assertEqual(cm.exception.message,
                             'Required config field token not provided.')
