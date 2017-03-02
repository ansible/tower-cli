# Copyright 2017 Ansible by Red Hat
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

import click

from tower_cli import models, resources
from tower_cli.api import client
from tower_cli.utils import debug, types, exceptions


class Resource(models.ExeResource):
    cli_help = 'Launch or monitor workflow jobs.'
    endpoint = '/workflow_jobs/'

    workflow_job_template = models.Field(
        key='-W',
        type=types.Related('workflow'),
        required=False, display=True
    )
    extra_vars = models.Field(
        key='-e',
        type=types.Variables(), required=False, display=False
    )
    created = models.Field(required=False, display=True)
    status = models.Field(required=False, display=True)

    @resources.command(
        use_fields_as_options=('workflow_job_template', 'extra_vars')
    )
    @click.option('--monitor', is_flag=True, default=False,
                  help='If sent, immediately calls monitor on the newly '
                       'launched workflow job rather than exiting.')
    @click.option('--timeout', required=False, type=int,
                  help='If provided with --monitor, this command (not the job)'
                       ' will time out after the given number of seconds. '
                       'Does nothing if --monitor is not sent.')
    def launch(self, workflow_job_template=None, monitor=False, timeout=None,
               extra_vars=None, **kwargs):
        """Launch a new workflow job based on a workflow job template.

        Creates a new workflow job in Ansible Tower, starts it, and
        returns back an ID in order for its status to be monitored.
        """
        if workflow_job_template is None:
            raise exceptions.BadRequest(
                'Must specify a workflow job template with -W option.'
            )
        debug.log('Launching the workflow job.', header='details')
        self._pop_none(kwargs)
        post_response = client.post('workflow_job_templates/{}/launch/'.format(
            workflow_job_template), data=kwargs).json()

        workflow_job_id = post_response['id']
        post_response['changed'] = True

        if monitor:
            return self.monitor(workflow_job_id, timeout=timeout)

        return post_response
