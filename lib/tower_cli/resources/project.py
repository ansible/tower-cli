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

import click

from sdict import adict

from tower_cli import models, resources
from tower_cli.api import client
from tower_cli.utils import debug, exceptions as exc, types


class Resource(models.MonitorableResource):
    cli_help = 'Manage projects within Ansible Tower.'
    endpoint = '/projects/'

    name = models.Field(unique=True)
    description = models.Field(required=False, display=False)
    organization = models.Field(type=types.Related('organization'),
                                display=False, required=False)
    scm_type = models.Field(
        type=types.MappedChoice([
            ('', 'manual'),
            ('git', 'git'),
            ('hg', 'hg'),
            ('svn', 'svn'),
        ]),
    )
    scm_url = models.Field(required=False)
    local_path = models.Field(
        help_text='For manual projects, the server playbook directory name',
        required=False)
    scm_branch = models.Field(required=False, display=False)
    scm_credential = models.Field(
        'credential', display=False, required=False,
        type=types.Related('credential'),
    )
    scm_clean = models.Field(type=bool, required=False, display=False)
    scm_delete_on_update = models.Field(type=bool, required=False,
                                        display=False)
    scm_update_on_launch = models.Field(type=bool, required=False,
                                        display=False)

    def create(self, *args, **kwargs):
        """Fix for issue #52, second method, replacing the /projects/
        endpoint temporarily if the project has an organization specified
        """
        if "organization" in kwargs:
            debug.log("using alternative endpoint for new project",
                      header='details')
            org_pk = kwargs['organization']
            self.endpoint = '/organizations/%s/projects/' % org_pk
        to_return = super(Resource, self).create(*args, **kwargs)
        self.endpoint = '/projects/'
        return to_return

    @resources.command(use_fields_as_options=('name', 'organization'))
    @click.option('--monitor', is_flag=True, default=False,
                  help='If sent, immediately calls `job monitor` on the newly '
                       'launched job rather than exiting with a success.')
    @click.option('--timeout', required=False, type=int,
                  help='If provided with --monitor, this command (not the job)'
                       ' will time out after the given number of seconds. '
                       'Does nothing if --monitor is not sent.')
    def update(self, pk, monitor=False, timeout=None, name=None,
                     organization=None):
        """Trigger a project update job within Ansible Tower.
        Only meaningful on non-manual projects.
        """
        # First, get the appropriate project.
        # This should be uniquely identified at this point, and if not, then
        # we just want the error that `get` will throw to bubble up.
        project = self.get(pk, name=name, organization=organization)
        pk = project['id']

        # Determine whether this project is able to be updated.
        debug.log('Asking whether the project can be updated.',
                  header='details')
        result = client.get('/projects/%d/update/' % pk)
        if not result.json()['can_update']:
            raise exc.CannotStartJob('Cannot update project.')

        # Okay, this project can be updated, according to Tower.
        # Commence the update.
        debug.log('Updating the project.', header='details')
        result = client.post('/projects/%d/update/' % pk)
        project_update_id = result.json()['project_update']

        # If we were told to monitor the project update's status, do so.
        if monitor:
            return self.monitor(pk, timeout=timeout)

        # Return the project update ID.
        return {
            'changed': True,
        }

    @resources.command
    @click.option('--detail', is_flag=True, default=False,
                              help='Print more detail.')
    def status(self, pk, detail=False):
        """Print the current job status."""
        # Get the job from Ansible Tower.
        debug.log('Asking for project update status.', header='details')
        project = client.get('/projects/%d/' % pk).json()

        # Determine the appropriate project update.
        if 'current_update' in project['related']:
            debug.log('A current update exists; retrieving it.',
                      header='details')
            job = client.get(project['related']['current_update'][7:]).json()
        elif project['related'].get('last_update', None):
            debug.log('No current update exists; retrieving the most '
                      'recent update.', header='details')
            job = client.get(project['related']['last_update'][7:]).json()
        else:
            raise exc.NotFound('No project updates exist.')

        # In most cases, we probably only want to know the status of the job
        # and the amount of time elapsed. However, if we were asked for
        # verbose information, provide it.
        if detail:
            return job

        # Print just the information we need.
        return adict({
            'elapsed': job['elapsed'],
            'failed': job['failed'],
            'status': job['status'],
        })
