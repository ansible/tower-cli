# Copyright 2015, Ansible, Inc.
# Alan Rominger <arominger@ansible.com>
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

from tests.compat import unittest, mock
from tower_cli.conf import settings

import click


class TemplateTests(unittest.TestCase):
    """A set of tests for commands operating on the job template
    """
    def setUp(self):
        self.res = tower_cli.get_resource('job_template')

    def test_create(self):
        """Establish that a job template can be created
        """
        with client.test_mode as t:
            endpoint = '/job_templates/'
            t.register_json(endpoint, {'count': 0, 'results': [],
                            'next': None, 'previous': None},
                            method='GET')
            t.register_json(endpoint, {'changed': True, 'id': 42},
                            method='POST')
            self.res.create(name='bar', job_type='run', inventory=1,
                            project=1, playbook='foobar.yml', credential=1)
            self.assertEqual(t.requests[0].method, 'GET')
            self.assertEqual(t.requests[1].method, 'POST')
            self.assertEqual(len(t.requests), 2)

    def test_job_template_create_with_echo(self):
        """Establish that a job template can be created
        """
        with client.test_mode as t:
            endpoint = '/job_templates/'
            t.register_json(endpoint, {'count': 0, 'results': [],
                            'next': None, 'previous': None},
                            method='GET')
            t.register_json(endpoint,
                            {'changed': True, 'id': 42,
                                'name': 'bar', 'inventory': 1, 'project': 1,
                                'playbook': 'foobar.yml', 'credential': 1},
                            method='POST')
            self.res.create(name='bar', job_type='run', inventory=1,
                            project=1, playbook='foobar.yml', credential=1)

            f = self.res.as_command()._echo_method(self.res.create)
            with mock.patch.object(click, 'secho'):
                with settings.runtime_values(format='human'):
                    f(name='bar', job_type='run', inventory=1,
                      project=1, playbook='foobar.yml', credential=1)

    def test_create_w_extra_vars(self):
        """Establish that a job template can be created
        and extra varas passed to it
        """
        with client.test_mode as t:
            endpoint = '/job_templates/'
            t.register_json(endpoint, {'count': 0, 'results': [],
                            'next': None, 'previous': None},
                            method='GET')
            t.register_json(endpoint, {'changed': True, 'id': 42},
                            method='POST')
            self.res.create(name='bar', job_type='run', inventory=1,
                            project=1, playbook='foobar.yml', credential=1,
                            extra_vars=['foo: bar'])
            self.assertEqual(t.requests[0].method, 'GET')
            self.assertEqual(t.requests[1].method, 'POST')
            self.assertEqual(len(t.requests), 2)

    def test_modify(self):
        """Establish that a job template can be modified
        """
        with client.test_mode as t:
            endpoint = '/job_templates/'
            t.register_json(endpoint, {'count': 1, 'results': [{'id': 1,
                            'name': 'bar'}], 'next': None, 'previous': None},
                            method='GET')
            t.register_json('/job_templates/1/', {'name': 'bar', 'id': 1,
                            'job_type': 'run'},
                            method='PATCH')
            self.res.modify(name='bar', playbook='foobared.yml')
            self.assertEqual(t.requests[0].method, 'GET')
            self.assertEqual(t.requests[1].method, 'PATCH')
            self.assertEqual(len(t.requests), 2)

    def test_modify_extra_vars(self):
        """Establish that a job template can be modified
        """
        with client.test_mode as t:
            endpoint = '/job_templates/'
            t.register_json(endpoint, {'count': 1, 'results': [{'id': 1,
                            'name': 'bar'}], 'next': None, 'previous': None},
                            method='GET')
            t.register_json('/job_templates/1/', {'name': 'bar', 'id': 1,
                            'job_type': 'run'},
                            method='PATCH')
            self.res.modify(name='bar', extra_vars="a: 5")
            self.assertEqual(t.requests[0].method, 'GET')
            self.assertEqual(t.requests[1].method, 'PATCH')
            self.assertEqual(len(t.requests), 2)
