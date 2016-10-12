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

import json
import yaml
import time
from copy import copy

import click

import tower_cli
from tower_cli.api import client
from tower_cli.utils import exceptions as exc

from tests.compat import unittest, mock
from tower_cli.conf import settings


# Standard functions used for space and readability
# these operate on the test client, t
def register_get(t):
    """ After starting job, the launch method may grab info about
    the job just launched from this endpoint """
    t.register_json('/jobs/42/',
                    {
                        'id': 42, 'job_template': 1, 'status': 'pending',
                        'created': 1234, 'elapsed': 0.0,
                    }, method='GET')


def standard_registration(t, **kwargs):
    """ Endpoints common to launching any job with template #1 and
    is automatically assigned to job #42. kwargs is used to provide
    extra return fields of job launch"""

    # A GET to the template endpoint is made to find the extra_vars to combine
    t.register_json('/job_templates/1/', {
        'id': 1,
        'name': 'frobnicate',
        'related': {'launch': '/job_templates/1/launch/'},
    })
    register_get(t)

    # A GET to the launch endpoint is needed to check if
    # a password prompt is needed
    t.register_json('/job_templates/1/launch/', {}, method='GET')

    # A POST to the launch endpoint will launch a job, and we
    # expect that the tower server will return the job number
    data = {'job': 42}
    data.update(kwargs)
    t.register_json('/job_templates/1/launch/', data, method='POST')


def jt_vars_registration(t, extra_vars):
    """ Endpoints that are needed to get information from job template.
    This particular combination also entails
    1) version of Tower - 2.2.0
    2) sucessful job launch, id=42
    3) prompts user for variables on launch """
    t.register_json('/job_templates/1/', {
        'ask_variables_on_launch': True,
        'extra_vars': extra_vars,
        'id': 1,
        'name': 'frobnicate',
        'related': {'launch': '/job_templates/1/launch/'},
    })
    register_get(t)
    t.register_json('/config/', {'version': '2.2.0'}, method='GET')
    t.register_json('/job_templates/1/launch/', {}, method='GET')
    t.register_json('/job_templates/1/launch/', {'job': 42},
                    method='POST')


class LaunchTests(unittest.TestCase):
    """A set of tests for ensuring that the job resource's launch command
    works in the way we expect.
    """
    def setUp(self):
        self.res = tower_cli.get_resource('job')

    def test_basic_launch(self):
        """Establish that we are able to create a job that doesn't require
        any invocation-time input.
        """
        with client.test_mode as t:
            standard_registration(t)
            result = self.res.launch(1)
            self.assertDictContainsSubset({'changed': True, 'id': 42}, result)

    def test_basic_launch_with_echo(self):
        """Establish that we are able to create a job and echo the output
        to the command line without it breaking.
        """
        with client.test_mode as t:
            standard_registration(t)
            result = self.res.launch(1)
            self.assertDictContainsSubset({'changed': True, 'id': 42}, result)

            f = self.res.as_command()._echo_method(self.res.launch)
            with mock.patch.object(click, 'secho'):
                with settings.runtime_values(format='human'):
                    f(job_template=1)

    def test_launch_w_tags(self):
        """Establish that we are able to create a job and attach tags to it.
        """
        with client.test_mode as t:
            standard_registration(t)
            self.res.launch(1, tags="a, b, c")
            self.assertEqual(
                json.loads(t.requests[2].body)['job_tags'], 'a, b, c',
            )

    def test_launch_w_tuple_extra_vars(self):
        """Establish that if the click library gives a tuple, than the job
        will run normally.
        """
        with client.test_mode as t:
            standard_registration(t)
            result = self.res.launch(1, extra_vars=())
            self.assertDictContainsSubset({'changed': True, 'id': 42}, result)

    def test_basic_launch_wait_option(self):
        """Establish that we are able to create a job that doesn't require
        any invocation-time input, and that wait is called if requested.
        """
        with client.test_mode as t:
            standard_registration(t)
            with mock.patch.object(type(self.res), 'wait') as wait:
                self.res.launch(1, wait=True)
                wait.assert_called_once_with(42, timeout=None)

    def test_extra_vars_at_runtime(self):
        """Establish that if we should be asking for extra variables at
        runtime, that we do.
        """
        with client.test_mode as t:
            # test with JSON job template extra_vars
            jt_vars_registration(t, '{"spam": "eggs"}')
            with mock.patch.object(click, 'edit') as edit:
                edit.return_value = '# Nothing.\nfoo: bar'
                result = self.res.launch(1, no_input=False)
                self.assertDictContainsSubset(
                    {"spam": "eggs"},
                    yaml.load(edit.mock_calls[0][1][0])
                )
            self.assertDictContainsSubset(
                {'foo': 'bar'},
                json.loads(json.loads(t.requests[3].body)['extra_vars'])
            )
            self.assertDictContainsSubset({'changed': True, 'id': 42}, result)

    def test_extra_vars_at_runtime_YAML_JT(self):
        """Establish that if we should be asking for extra variables at
        runtime, that we do.
        """
        with client.test_mode as t:
            # test with YAML and comments
            jt_vars_registration(t, 'spam: eggs\n# comment')
            with mock.patch.object(click, 'edit') as edit:
                edit.return_value = '# Nothing.\nfoo: bar'
                self.res.launch(1, no_input=False)
                self.assertIn('# comment', edit.mock_calls[0][1][0])
                self.assertDictContainsSubset(
                    {"spam": "eggs"},
                    yaml.load(edit.mock_calls[0][1][0])
                )

    def test_extra_vars_at_runtime_no_user_data(self):
        """User launches a job that prompts for variables. User closes
        editor without adding any text.
        Establish that we launch the job as-is.
        """
        with client.test_mode as t:
            # No job template variables
            jt_vars_registration(t, '')
            initial = '\n'.join((
                '# Specify extra variables (if any) here as YAML.',
                '# Lines beginning with "#" denote comments.',
                '',
            ))
            with mock.patch.object(click, 'edit') as edit:
                edit.return_value = initial
                self.res.launch(1, no_input=False)
                self.assertEqual(t.requests[2].method, 'POST')
                self.assertEqual(t.requests[2].body, '{}')

    def test_job_template_variables(self):
        """Establish that job template extra_vars are combined with local
        extra vars, but only for older versions
        """
        with client.test_mode as t:
            jt_vars_registration(t, 'spam: eggs')
            result = self.res.launch(1, extra_vars=['foo: bar'])
            response_json = yaml.load(t.requests[3].body)
            ev_json = yaml.load(response_json['extra_vars'])
            self.assertTrue('foo' in ev_json)
            self.assertTrue('spam' in ev_json)
            self.assertDictContainsSubset({'changed': True, 'id': 42}, result)

    def test_job_template_variables_post_24(self):
        """ Check that in recent versions, it does not include job template
         variables along with the rest """
        with client.test_mode as t:
            jt_vars_registration(t, 'spam: eggs')
            t.register_json('/config/', {'version': '2.4'}, method='GET')
            result = self.res.launch(1, extra_vars=['foo: bar'])
            response_json = yaml.load(t.requests[3].body)
            ev_json = yaml.load(response_json['extra_vars'])
            self.assertTrue('foo' in ev_json)
            self.assertTrue('spam' not in ev_json)
            self.assertDictContainsSubset({'changed': True, 'id': 42}, result)

    def test_extra_vars_at_runtime_tower_20(self):
        """Establish that if we should be asking for extra variables at
        runtime, that we do.
        (This test is intended for Tower 2.0 compatibility.)
        """
        with client.test_mode as t:
            t.register_json('/job_templates/1/', {
                'ask_variables_on_launch': True,
                'extra_vars': 'spam: eggs',
                'id': 1,
                'name': 'frobnicate',
                'related': {},
            })
            register_get(t)
            t.register_json('/config/', {'version': '2.0'}, method='GET')
            t.register_json('/jobs/', {'id': 42}, method='POST')
            t.register_json('/jobs/42/start/', {}, method='GET')
            t.register_json('/jobs/42/start/', {}, method='POST')
            with mock.patch.object(click, 'edit') as edit:
                edit.return_value = '# Nothing.\nfoo: bar'
                result = self.res.launch(1, no_input=False)
                self.assertDictContainsSubset(
                    {"spam": "eggs"},
                    yaml.load(edit.mock_calls[0][1][0])
                )
            self.assertDictContainsSubset(
                {'foo': 'bar'},
                json.loads(json.loads(t.requests[2].body)['extra_vars'])
            )
            self.assertDictContainsSubset({'changed': True, 'id': 42}, result)

    def test_extra_vars_at_call_time(self):
        """Establish that extra variables specified at call time are
        appropriately specified.
        """
        with client.test_mode as t:
            t.register_json('/job_templates/1/', {
                'id': 1,
                'name': 'frobnicate',
                'related': {'launch': '/job_templates/1/launch/'},
            })
            register_get(t)
            t.register_json('/job_templates/1/launch/', {}, method='GET')
            t.register_json('/job_templates/1/launch/', {'job': 42},
                            method='POST')
            result = self.res.launch(1, extra_vars=['foo: bar'])

            self.assertDictContainsSubset(
                {'foo': 'bar'},
                json.loads(json.loads(t.requests[2].body)['extra_vars'])
            )
            self.assertDictContainsSubset({'changed': True, 'id': 42}, result)

    def test_extra_vars_file_at_call_time(self):
        """Establish that extra variables specified at call time as a file are
        appropriately specified.
        """
        with client.test_mode as t:
            t.register_json('/job_templates/1/', {
                'id': 1,
                'name': 'frobnicate',
                'related': {'launch': '/job_templates/1/launch/'},
            })
            register_get(t)
            t.register_json('/job_templates/1/launch/', {}, method='GET')
            t.register_json('/job_templates/1/launch/', {'job': 42},
                            method='POST')
            result = self.res.launch(1, extra_vars=['foo: bar'])

            self.assertDictContainsSubset(
                {'foo': 'bar'},
                json.loads(json.loads(t.requests[2].body)['extra_vars'])
            )
            self.assertDictContainsSubset({'changed': True, 'id': 42}, result)

    def test_passwords_needed_at_start(self):
        """Establish that we are able to create a job that doesn't require
        any invocation-time input.
        """
        with client.test_mode as t:
            t.register_json('/job_templates/1/', {
                'id': 1,
                'name': 'frobnicate',
                'related': {'launch': '/job_templates/1/launch/'},
            })
            register_get(t)
            t.register_json('/job_templates/1/launch/', {
                'passwords_needed_to_start': ['foo'],
            }, method='GET')
            t.register_json('/job_templates/1/launch/', {'job': 42},
                            method='POST')

            with mock.patch('tower_cli.resources.job.getpass') as getpass:
                getpass.return_value = 'bar'
                result = self.res.launch(1)
                getpass.assert_called_once_with('Password for foo: ')
            self.assertDictContainsSubset({'changed': True, 'id': 42}, result)

    def test_launch_with_use_job_endpoint_set(self):
        """Establish that launching a job with `--use-job-endpoint` set would
        launch job through /jobs/\d/ endpoint regardless of the existance of
        /job_templates/\d/launch/ endpoint
        """
        jt = {
            'related': {
                'launch': '/api/v1/job_templates/1/launch/'
            },
            'id': 1,
            'name': 'demo'
        }
        with client.test_mode as t:
            t.register_json('/job_templates/1/', jt)
            t.register_json('/jobs/16/', {})
            t.register_json('/jobs/', {'id': 16}, method='POST')
            t.register_json('/jobs/16/start/', {})
            t.register_json('/jobs/16/start/', {}, method='POST')
            self.res.launch(job_template=1, use_job_endpoint=True)

    def test_ignored_fields(self):
        """Establish that if ignored_fields is returned when launching job,
        it will be displayed in verbose mode.
        """
        echo_count_with_ignore = 0
        echo_count = 0
        with client.test_mode as t:
            standard_registration(t)
            with settings.runtime_values(verbose=True):
                with mock.patch.object(click, 'secho') as secho:
                    self.res.launch(job_template=1)
                echo_count = secho.call_count
        with client.test_mode as t:
            standard_registration(t, ignored_fields={'foo': 'bar'})
            with settings.runtime_values(verbose=True):
                with mock.patch.object(click, 'secho') as secho:
                    self.res.launch(job_template=1)
                echo_count_with_ignore = secho.call_count
        self.assertEqual(echo_count_with_ignore - echo_count, 2)


class StatusTests(unittest.TestCase):
    """A set of tests to establish that the job status command works in the
    way that we expect.
    """
    def setUp(self):
        self.res = tower_cli.get_resource('job')

    def test_normal(self):
        """Establish that the data about a job retrieved from the jobs
        endpoint is provided.
        """
        with client.test_mode as t:
            t.register_json('/jobs/42/', {
                'elapsed': 1335024000.0,
                'extra': 'ignored',
                'failed': False,
                'status': 'successful',
            })
            result = self.res.status(42)
            self.assertEqual(result, {
                'elapsed': 1335024000.0,
                'failed': False,
                'status': 'successful',
            })
            self.assertEqual(len(t.requests), 1)

    def test_normal_with_lookup(self):
        """Establish that the data about job specified by query is
        returned correctly.
        """
        with client.test_mode as t:
            t.register_json('/jobs/?name=bar', {"count": 1, "results": [
                {"id": 42, "name": "bar",
                    'elapsed': 1335024000.0,
                    'extra': 'ignored',
                    'failed': False,
                    'status': 'successful', },
            ], "next": None, "previous": None}, method='GET')
            result = self.res.status(name="bar")
            self.assertEqual(result, {
                'elapsed': 1335024000.0,
                'failed': False,
                'status': 'successful',
            })
            self.assertEqual(len(t.requests), 1)

    def test_detailed(self):
        with client.test_mode as t:
            t.register_json('/jobs/42/', {
                'elapsed': 1335024000.0,
                'extra': 'ignored',
                'failed': False,
                'status': 'successful',
            })
            result = self.res.status(42, detail=True)
            self.assertEqual(result, {
                'elapsed': 1335024000.0,
                'extra': 'ignored',
                'failed': False,
                'status': 'successful',
            })
            self.assertEqual(len(t.requests), 1)


class MonitorWaitTests(unittest.TestCase):
    """A set of tests to establish that the job monitor and wait commands
    works in the way that we expect.
    """
    def setUp(self):
        self.res = tower_cli.get_resource('job')

    def test_already_successful(self):
        """Establish that if we attempt to wait an already successful job,
        we simply get back the job success report.
        """
        with client.test_mode as t:
            t.register_json('/jobs/42/', {
                'elapsed': 1335024000.0,
                'failed': False,
                'status': 'successful',
            })
            with mock.patch.object(time, 'sleep') as sleep:
                result = self.res.wait(42)
                self.assertEqual(sleep.call_count, 0)
                self.assertEqual(result['status'], 'successful')

    def test_already_successful_monitor(self):
        """Pass-through sucessful job with monitor method"""
        with client.test_mode as t:
            t.register_json('/jobs/42/', {
                'elapsed': 1335024000.0,
                'failed': False,
                'status': 'successful',
            })
            # Test same for monitor
            with mock.patch.object(time, 'sleep') as sleep:
                with mock.patch.object(type(self.res), 'wait'):
                    with mock.patch.object(click, 'echo'):
                        result = self.res.monitor(42)
                        self.assertEqual(sleep.call_count, 0)
                        self.assertEqual(result['status'], 'successful')

    def test_failure(self):
        """Establish that if the job has failed, that we raise the
        JobFailure exception.
        """
        with client.test_mode as t:
            t.register_json('/jobs/42/', {
                'elapsed': 1335024000.0,
                'failed': True,
                'status': 'failed',
            })
            with self.assertRaises(exc.JobFailure):
                with mock.patch.object(click, 'secho') as secho:
                    with mock.patch('tower_cli.models.base.is_tty') as tty:
                        tty.return_value = True
                        self.res.wait(42)
                self.assertTrue(secho.call_count >= 1)
            # Test the same with the monitor method
            with self.assertRaises(exc.JobFailure):
                with mock.patch.object(click, 'secho') as secho:
                    with mock.patch('tower_cli.models.base.is_tty') as tty:
                        tty.return_value = True
                        self.res.monitor(42)
                self.assertTrue(secho.call_count >= 1)

    def test_failure_non_tty(self):
        """Establish that if the job has failed, that we raise the
        JobFailure exception, and also don't print bad things on non-tty
        outfiles.
        """
        with client.test_mode as t:
            t.register_json('/jobs/42/', {
                'elapsed': 1335024000.0,
                'failed': True,
                'status': 'failed',
            })
            with self.assertRaises(exc.JobFailure):
                with mock.patch.object(click, 'echo') as echo:
                    with mock.patch('tower_cli.models.base.is_tty') as tty:
                        tty.return_value = False
                        self.res.wait(42)
                self.assertTrue(echo.call_count >= 1)

    def test_waiting(self):
        """Establish that if the first status call returns a pending job,
        and the second a success, that both calls are made, and a success
        finally returned.
        """
        # Set up our data object.
        data = {'elapsed': 1335024000.0, 'failed': False, 'status': 'pending'}

        # Register the initial request's response.
        with client.test_mode as t:
            t.register_json('/jobs/42/', copy(data))

            # Create a way to assign a successful data object to the request.
            def assign_success(*args):
                t.clear()
                t.register_json('/jobs/42/', dict(data, status='successful'))

            # Make the successful state assignment occur when time.sleep()
            # is called between requests.
            with mock.patch.object(time, 'sleep') as sleep:
                sleep.side_effect = assign_success
                with mock.patch.object(click, 'secho') as secho:
                    with mock.patch('tower_cli.models.base.is_tty') as tty:
                        tty.return_value = True
                        self.res.wait(42, min_interval=0.21)
                self.assertTrue(secho.call_count >= 100)

            # We should have gotten two requests total, to the same URL.
            self.assertEqual(len(t.requests), 2)
            self.assertEqual(t.requests[0].url, t.requests[1].url)

    def test_monitor(self):
        """Establish that if the first status call returns a pending job,
        and the second a success, that both calls are made, and a success
        finally returned.
        """
        # Set up our data object.
        data = {'elapsed': 1335024000.0, 'failed': False, 'status': 'pending'}

        # Register the initial request's response.
        with client.test_mode as t:
            t.register_json('/jobs/42/', copy(data))

            # Create a way to assign a successful data object to the request.
            def assign_success(*args):
                t.clear()
                t.register_json('/jobs/42/', dict(data, status='successful'))

            # Make the successful state assignment occur when time.sleep()
            # is called between requests.
            with mock.patch.object(time, 'sleep') as sleep:
                sleep.side_effect = assign_success
                with mock.patch.object(click, 'echo'):
                    with mock.patch.object(type(self.res), 'wait'):
                        with mock.patch.object(
                                type(self.res), 'lookup_stdout'):
                            self.res.monitor(42, min_interval=0.21)

            # We should have gotten 3 requests total, to the same URL.
            self.assertEqual(len(t.requests), 3)
            self.assertEqual(t.requests[0].url, t.requests[1].url)

    def test_timeout(self):
        """Establish that the --timeout flag is honored if sent to
        `tower-cli job wait`.
        """
        # Set up our data object.
        # This doesn't have to change; it will always be pending
        # (thus the timeout).
        data = {'elapsed': 1335024000.0, 'failed': False, 'status': 'pending'}

        # Mock out the passage of time.
        with client.test_mode as t:
            t.register_json('/jobs/42/', copy(data))
            with mock.patch.object(click, 'secho') as secho:
                with self.assertRaises(exc.Timeout):
                    with mock.patch('tower_cli.models.base.is_tty') as tty:
                        tty.return_value = True
                        self.res.wait(42, min_interval=0.21, timeout=0.1)
                self.assertTrue(secho.call_count >= 1)

    def test_waiting_not_tty(self):
        """Establish that the wait command prints more useful output
        for logging if not connected to a tty.
        """
        # Set up our data object.
        data = {'elapsed': 1335024000.0, 'failed': False, 'status': 'pending'}

        # Register the initial request's response.
        with client.test_mode as t:
            t.register_json('/jobs/42/', copy(data))

            # Create a way to assign a successful data object to the request.
            def assign_success(*args):
                t.clear()
                t.register_json('/jobs/42/', dict(data, status='successful'))

            # Make the successful state assignment occur when time.sleep()
            # is called between requests.
            with mock.patch.object(time, 'sleep') as sleep:
                sleep.side_effect = assign_success
                with mock.patch.object(click, 'echo') as echo:
                    with mock.patch('tower_cli.models.base.is_tty') as tty:
                        tty.return_value = False
                        self.res.wait(42, min_interval=0.21)
                self.assertTrue(echo.call_count >= 1)

            # We should have gotten two requests total, to the same URL.
            self.assertEqual(len(t.requests), 2)
            self.assertEqual(t.requests[0].url, t.requests[1].url)


class CancelTests(unittest.TestCase):
    """A set of tasks to establish that the job cancel command works in the
    way that we expect.
    """
    def setUp(self):
        self.res = tower_cli.get_resource('job')

    def test_standard_cancelation(self):
        """Establish that a standard cancelation command works in the way
        we expect.
        """
        with client.test_mode as t:
            t.register('/jobs/42/cancel/', '', method='POST')
            result = self.res.cancel(42)
            self.assertTrue(t.requests[0].url.endswith('/jobs/42/cancel/'))
            self.assertTrue(result['changed'])

    def test_cancelation_by_lookup(self):
        """Establish that a job can be canceled by name or identity
        """
        with client.test_mode as t:
            t.register_json('/jobs/?name=bar', {"count": 1, "results": [
                {"id": 42, "name": "bar"},
            ], "next": None, "previous": None}, method='GET')
            t.register('/jobs/42/cancel/', '', method='POST')
            result = self.res.cancel(name="bar")
            self.assertTrue(t.requests[0].url.endswith('/jobs/?name=bar'))
            self.assertTrue(t.requests[1].url.endswith('/jobs/42/cancel/'))
            self.assertTrue(result['changed'])

    def test_cancelation_completed(self):
        """Establish that a standard cancelation command works in the way
        we expect.
        """
        with client.test_mode as t:
            t.register('/jobs/42/cancel/', '', method='POST', status_code=405)
            result = self.res.cancel(42)
            self.assertTrue(t.requests[0].url.endswith('/jobs/42/cancel/'))
            self.assertFalse(result['changed'])

    def test_cancelation_completed_with_error(self):
        """Establish that a standard cancelation command works in the way
        we expect.
        """
        with client.test_mode as t:
            t.register('/jobs/42/cancel/', '', method='POST', status_code=405)
            with self.assertRaises(exc.TowerCLIError):
                self.res.cancel(42, fail_if_not_running=True)
