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
from tower_cli.utils import exceptions as exc

from tests.compat import unittest, mock


class CreateTests(unittest.TestCase):
    """A set of tests for ensuring that the project resource's create command
    works in the way we expect.
    """
    def setUp(self):
        self.res = tower_cli.get_resource('project')

    def test_create_with_organization(self):
        """Establish that a project can be created inside of an organization.
        This uses the --organization flag with the create command.
        """
        with client.test_mode as t:
            t.register_json('/projects/', {'count': 0, 'results': [],
                            'next': None, 'previous': None},
                            method='GET')
            # OPTIONS check is used to determine how the linkage is done
            t.register_json('/projects/', {'actions': {'POST': {}}},
                            method='OPTIONS')
            t.register_json('/projects/', {'id': 42}, method='POST')
            # The org endpoint can be used to lookup org pk given org name
            t.register_json('/organizations/1/', {'id': 1}, method='GET')
            # This is an endpoint used for project-org association
            t.register_json(
                '/organizations/1/projects/', {'count': 0}, method='GET'
            )
            t.register_json(
                '/organizations/1/projects/', {'changed': True}, method='POST'
            )
            result = self.res.create(
                name='bar', organization=1, scm_type="git"
            )
            self.assertEqual(len(t.requests), 6)
            self.assertEqual(t.requests[0].method, 'OPTIONS')
            self.assertEqual(t.requests[1].method, 'GET')
            self.assertEqual(t.requests[2].method, 'POST')
            self.assertEqual(t.requests[3].method, 'GET')
            self.assertEqual(t.requests[4].method, 'GET')
            self.assertEqual(t.requests[5].method, 'POST')
            self.assertDictContainsSubset({'id': 42}, result)

    def test_create_with_organization_as_flag(self):
        """Establish organization works as direct API flag when the API
        allows for this use type."""
        with client.test_mode as t:
            t.register_json('/projects/', {'count': 0, 'results': [],
                            'next': None, 'previous': None},
                            method='GET')
            # OPTIONS check is used to determine how the linkage is done
            t.register_json(
                '/projects/', {'actions': {'POST': {
                    'organization': 'detail'}}}, method='OPTIONS')
            t.register_json('/projects/', {'id': 42}, method='POST')
            # The org endpoint can be used to lookup org pk given org name
            # t.register_json('/organizations/1/', {'id': 1}, method='GET')
            result = self.res.create(
                name='bar', organization=1, scm_type="git"
            )
            self.assertEqual(len(t.requests), 3)
            self.assertEqual(t.requests[0].method, 'OPTIONS')
            self.assertEqual(t.requests[1].method, 'GET')
            self.assertEqual(t.requests[2].method, 'POST')
            self.assertDictContainsSubset({'id': 42}, result)

    def test_create_without_organization(self):
        """Establish that a project can be created without giving an
        organization. This should create a project with no organization.
        This action uses the /projects/ endpoint
        """
        with client.test_mode as t:
            endpoint = '/projects/'
            t.register_json(endpoint, {'count': 0, 'results': [],
                            'next': None, 'previous': None},
                            method='GET')
            t.register_json(endpoint, {'changed': True, 'id': 42},
                            method='POST')
            self.res.create(name='bar', scm_type="git")
            self.assertEqual(t.requests[0].method, 'GET')
            self.assertEqual(t.requests[1].method, 'POST')
            self.assertEqual(len(t.requests), 2)

    def test_create_wait(self):
        """Establish that a project can be created with the wait flag
        enabled and still sucessfully exit and complete.
        """
        with client.test_mode as t:

            # Endpoints related to creating the resource
            t.register_json('/projects/', {'count': 0, 'results': [],
                            'next': None, 'previous': None},
                            method='GET')
            t.register_json('/projects/', {'changed': True, 'id': 42},
                            method='POST')
            # Endpoints related to waiting for the resource
            t.register_json(
                '/projects/42/', {
                    'status': 'successful',
                    'related': {'last_update': '/api/v1/project_updates/21/'}
                },
                method='GET'
            )
            t.register_json(
                '/project_updates/21/', {'id': 21, 'status': 'successful'},
                method='GET'
            )

            result = self.res.create(name='bar', scm_type="git", wait=True)
            self.assertEqual(t.requests[0].method, 'GET')
            self.assertEqual(t.requests[-1].method, 'GET')
            self.assertDictContainsSubset({'changed': True}, result)


class UpdateTests(unittest.TestCase):
    """A set of tests for ensuring that the project resource's update command
    works in the way we expect.
    """
    def setUp(self):
        self.res = tower_cli.get_resource('project')

    def test_modify_project(self):
        """Test modifying project in order to cover the special case that
        removes the organization from its options.
        """
        with client.test_mode as t:
            t.register_json('/projects/', {'count': 1, 'results': [{'id': 1,
                            'name': 'bar'}], 'next': None, 'previous': None},
                            method='GET')
            t.register_json('/projects/1/', {'name': 'bar', 'id': 1,
                            'type': 'project', 'organization': 1},
                            method='PATCH')
            self.res.modify(name='bar', scm_type="git")
            self.assertEqual(t.requests[0].method, 'GET')
            self.assertEqual(t.requests[1].method, 'PATCH')
            self.assertEqual(len(t.requests), 2)

    def test_basic_update(self):
        """Establish that we are able to create a project update
        and return the changed status.
        """
        with client.test_mode as t:
            t.register_json('/projects/1/', {
                'id': 1,
                'name': 'frobnicate',
                'related': {'update': '/api/v1/projects/1/update/'},
            })
            t.register_json('/projects/1/update/', {'can_update': True},
                            method='GET')
            t.register_json('/projects/1/update/', {'project_update': 42},
                            method='POST')
            result = self.res.update(1)
            self.assertEqual(result, {'changed': True})

    def test_basic_update_with_monitor(self):
        """Establish that we are able to create a project update
        and shift to monitoring if requested.
        """
        with client.test_mode as t:
            t.register_json('/projects/1/', {
                'id': 1,
                'name': 'frobnicate',
                'related': {'update': '/api/v1/projects/1/update/'},
            })
            t.register_json('/projects/1/update/', {'can_update': True},
                            method='GET')
            t.register_json('/projects/1/update/', {'project_update': 42},
                            method='POST')
            with mock.patch.object(type(self.res), 'monitor') as monitor:
                self.res.update(1, monitor=True)
                monitor.assert_called_once_with(42, parent_pk=1, timeout=None)
            # Test wait method, which follows same pattern
            with mock.patch.object(type(self.res), 'wait') as wait:
                self.res.update(1, wait=True)
                wait.assert_called_once_with(42, parent_pk=1, timeout=None)

    def test_cannot_update(self):
        """Establish that attempting to update a non-updatable project
        errors out as expected.
        """
        with client.test_mode as t:
            t.register_json('/projects/1/', {
                'id': 1,
                'name': 'frobnicate',
                'related': {'update': '/api/v1/projects/1/update/'},
            })
            t.register_json('/projects/1/update/', {'can_update': False},
                            method='GET')
            with self.assertRaises(exc.CannotStartJob):
                self.res.update(1)


class StatusTests(unittest.TestCase):
    """A set of tests to establish that the project status command works in
    the way that we expect.
    """
    def setUp(self):
        self.res = tower_cli.get_resource('project')

    def test_normal(self):
        """Establish that the data about a project update retrieved from the
        project updates endpoint is provided.
        """
        with client.test_mode as t:
            t.register_json('/projects/1/', {
                'id': 1,
                'related': {'last_update':
                            '/api/v1/projects/1/project_updates/42/'},
            })
            t.register_json('/projects/1/project_updates/42/', {
                'elapsed': 1335024000.0,
                'extra': 'ignored',
                'failed': False,
                'status': 'successful',
            })
            result = self.res.status(1)
            self.assertEqual(result, {
                'elapsed': 1335024000.0,
                'failed': False,
                'status': 'successful',
            })
            self.assertEqual(len(t.requests), 2)

    def test_detailed(self):
        """Establish that a detailed request is sent back in the way
        that we expect.
        """
        with client.test_mode as t:
            t.register_json('/projects/1/', {
                'id': 1,
                'related': {'last_update':
                            '/api/v1/projects/1/project_updates/42/'},
            })
            t.register_json('/projects/1/project_updates/42/', {
                'elapsed': 1335024000.0,
                'extra': 'ignored',
                'failed': False,
                'status': 'successful',
            })
            result = self.res.status(1, detail=True)
            self.assertEqual(result, {
                'elapsed': 1335024000.0,
                'extra': 'ignored',
                'failed': False,
                'status': 'successful',
            })
            self.assertEqual(len(t.requests), 2)

    def test_currently_running_update(self):
        """Establish that if an update is currently running, that we see this
        and send back the appropriate status.
        """
        with client.test_mode as t:
            t.register_json('/projects/1/', {
                'id': 1,
                'related': {
                    'current_update': '/api/v1/projects/1/project_updates/42/',
                    'last_update': '/api/v1/projects/1/project_updates/41/',
                },
            })
            t.register_json('/projects/1/project_updates/42/', {
                'elapsed': 1335024000.0,
                'extra': 'ignored',
                'failed': False,
                'status': 'running',
            })
            result = self.res.status(1)
            self.assertEqual(result, {
                'elapsed': 1335024000.0,
                'failed': False,
                'status': 'running',
            })
            self.assertEqual(len(t.requests), 2)

    def test_no_updates(self):
        """Establish that running `status` against a project with no updates
        raises the error we expect.
        """
        with client.test_mode as t:
            t.register_json('/projects/1/', {
                'id': 1,
                'related': {},
            })
            with self.assertRaises(exc.NotFound):
                self.res.status(1)
