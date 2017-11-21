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

import tower_cli
from tower_cli.api import client

from tests.compat import unittest, mock


class HostTests(unittest.TestCase):
    """Establish that the host resource methods work in the way
    that we expect.
    """
    def setUp(self):
        self.host_resource = tower_cli.get_resource('host')

    def test_list_under_group(self):
        """Establish that a group flag is converted into query string."""
        with mock.patch('tower_cli.models.base.BaseResource.list') as mock_list:
            self.host_resource.list(group=78)
            mock_list.assert_called_once_with(query=(('groups__in', 78),))

    def test_list_by_host_filter(self):
        """Establish that a host filter option is converted into query string."""
        with mock.patch('tower_cli.models.base.BaseResource.list') as mock_list:
            self.host_resource.list(host_filter='foobar')
            mock_list.assert_called_once_with(query=(('host_filter', 'foobar'),))

    def test_normal_list(self):
        """Establish that the group flag doesn't break the normal list."""
        with mock.patch('tower_cli.models.base.BaseResource.list') as mock_list:
            self.host_resource.list(name="foobar")
            mock_list.assert_called_once_with(name="foobar")

    def test_list_facts(self):
        """Establish that the list_facts command runs as it is supposed."""
        with client.test_mode as t:
            t.register_json('/hosts/42/', {'id': 42})
            t.register_json('/hosts/42/ansible_facts/', {'foo': 'bar'})
            self.assertEqual(self.host_resource.list_facts(pk=42), {'foo': 'bar'})

    def test_insights(self):
        """Establish that the insights command runs as it is supposed."""
        with client.test_mode as t:
            t.register_json('/hosts/42/', {'id': 42})
            t.register_json('/hosts/42/insights/', {'foo': 'bar'})
            self.assertEqual(self.host_resource.insights(pk=42), {'foo': 'bar'})
