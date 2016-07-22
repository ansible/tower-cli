# Copyright 2016, Ansible, Inc.
# Aaron Tan <sitan@ansible.com>
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


class LabelTests(unittest.TestCase):
    """A set of tests to establish that the label resource functions in the
    way that we expect.
    """
    def setUp(self):
        self.res = tower_cli.get_resource('label')

    def test_delete_method_is_disabled(self):
        """Establish that delete method of a label is properly disabled.
        """
        self.assertEqual(self.res.as_command().get_command(None, 'delete'),
                         None)

    def test_create_with_jt(self):
        """Establish that create a label with job template specified
        works in the way that we expect.
        """
        with client.test_mode as t:
            t.register_json('/job_templates/6/', {})
            t.register_json('/job_templates/6/labels/?name=foo',
                            {'count': 0, 'results': []})
            t.register_json('/job_templates/6/labels/', {'id': 1},
                            method='POST', status_code=201)
            t.register_json('/labels/?name=foo&organization=1',
                            {'count': 0, 'results': []})
            r = self.res.create(name='foo', organization=1, job_template=6)
            self.assertEqual(dict(r), {'id': 1, 'changed': True})
            t.register_json('/labels/?name=foo&organization=1',
                            {'count': 1, 'results': [{'id': 1}]})
            with self.assertRaises(exc.TowerCLIError):
                self.res.create(name='foo', organization=1, job_template=6,
                                fail_on_found=True)
