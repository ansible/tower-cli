# Copyright 2016, Ansible by Red Hat.
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
from tower_cli.models.base import Resource

from tests.compat import unittest

import json

CURD_METHODS = ('create', 'modify', 'list', 'get', 'delete')
CLICK_ATTRS = ('__click_params__', '_cli_command', '_cli_command_attrs')


class ScheduleTests(unittest.TestCase):
    """A set of tests for commands operating on schedules
    """
    def setUp(self):
        self.res = tower_cli.get_resource('schedule')
        self.endpoint = '/schedules/'

    def test_raises_with_duplicate_unified_jt_fields(self):
        """Establish that No more than one unified job template fields
        should be provided.
        """
        with self.assertRaises(exc.UsageError) as cm:
            self.res.get(job_template=1, project=2)
        self.assertEqual(cm.exception.message, 'More than one unified job'
                         ' template fields provided, please tighten your '
                         'criteria.')

    def test_raises_with_no_unified_jt_fields_during_creation(self):
        """Establish that At least one unified job template field should
        be provided during creation.
        """
        with self.assertRaises(exc.UsageError) as cm:
            self.res.create(name='hehe')
        self.assertEqual(cm.exception.message, 'You must provide exactly '
                         'one unified job template field during creation.')

    def test_decorated_methods_have_click_related_attributes(self):
        """Establish that click-related extra function attributes are passed
        on to decorated methods.
        """
        for item in CURD_METHODS:
            method = getattr(self.res, item)
            for attr in CLICK_ATTRS:
                self.assertIn(attr, dir(method))

    def test_docstring_is_passed(self):
        """Establish that docstring of the original method are passed on
        to decorated counterpart.
        """
        parent_res = Resource()
        for item in CURD_METHODS:
            method = getattr(self.res, item)
            parent_method = getattr(parent_res, item)
            self.assertEqual(method.__doc__, parent_method.__doc__)

    def test_create_invokes_correct_endpoint(self):
        """Establish that correct endpoint is invoked according to unified jt
        field provided during creation.
        """
        post_body = """
        {"name": "hehe", "unified_job_template": 5,
        "rrule": "DTSTART:20160812T200122Z"}
        """
        with client.test_mode as t:
            t.register_json('/job_templates/5/schedules/?name=hehe',
                            {'count': 0, 'results': []})
            t.register_json('/job_templates/5/schedules/', {'id': 5},
                            method='POST')
            self.res.create(name='hehe', job_template=5,
                            rrule='DTSTART:20160812T200122Z')
            self.assertEqual(json.loads(t.requests[1].body),
                             json.loads(post_body))
