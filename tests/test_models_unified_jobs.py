# Copyright 2016, Ansible by Red Hat
# Alan Rominger <arominge@redhat.com>
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

import time
import click

import tower_cli
from tower_cli.api import client

from tests.compat import unittest, mock


def project_update_registration(t):
    t.register_json('/project_updates/54/', {
        'elapsed': 1335024000.0,
        'failed': False,
        'status': 'successful',
    }, method='GET')


class StandardOutTests(unittest.TestCase):
    """
    Test that standard out lookup and wrapper methods
    """
    def setUp(self):
        # Representative of a Unified Job Template
        self.res = tower_cli.get_resource('project')
        # Representative of a Unified Job
        self.job_res = tower_cli.get_resource('job')

    def test_lookup_stdout(self):
        "Test the method that makes a call to get standard out."
        with client.test_mode as t:
            # note:
            # 'foobar' = 'Zm9vYmFy' via
            # base64.standard_b64encode('foobar'.encode('ascii'))
            # but python versions can't all agree on how to trim the string
            t.register_json(
                '/project_updates/42/stdout/',
                {'content': 'Zm9vYmFy'}, method='GET')
            stdout = self.res.lookup_stdout(42, start_line=0, end_line=1)
            assert 'foobar' in str(stdout)

    def test_stdout(self):
        "Test that printing standard out works with project-like things."
        with mock.patch.object(type(self.res), 'lookup_stdout') as lookup:
            with mock.patch.object(type(self.res), 'last_job_data') as job:
                with mock.patch.object(click, 'echo') as mock_echo:
                    job.return_value = {'id': 42}
                    lookup.return_value = 'foobar'
                    result = self.res.stdout(42)
                    assert not result['changed']
                    mock_echo.assert_called_once_with('foobar', nl=1)

    def test_stdout_with_lookup(self):
        "Test that unified job will be automatically looked up."
        with mock.patch.object(type(self.job_res), 'lookup_stdout'):
            with mock.patch.object(type(self.job_res), 'get') as get:
                with mock.patch.object(click, 'echo'):
                    self.job_res.stdout(pk=None, name="test-proj")
                    get.assert_called_once_with(name="test-proj")

    def test_call_wait_with_parent(self):
        "Test auto-lookup of last job is called for wait"
        with client.test_mode as t:
            project_update_registration(t)
            with mock.patch.object(type(self.res), 'last_job_data') as job:
                job.return_value = {'id': 54}
                with mock.patch.object(click, 'echo'):
                    with mock.patch.object(time, 'sleep'):
                        self.res.wait(pk=None, parent_pk=42)
                        job.assert_called_once_with(42)

    def test_call_monitor_with_parent(self):
        "Test auto-lookup when the monitor method is called"
        with client.test_mode as t:
            project_update_registration(t)
            with mock.patch.object(type(self.res), 'last_job_data') as job:
                job.return_value = {'id': 54}
                with mock.patch.object(click, 'echo'):
                    with mock.patch.object(type(self.res), 'wait'):
                        with mock.patch.object(time, 'sleep'):
                            self.res.monitor(pk=None, parent_pk=42)
                            job.assert_called_once_with(42)
