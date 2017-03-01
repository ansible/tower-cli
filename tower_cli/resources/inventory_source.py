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

from tower_cli import models, resources
from tower_cli.api import client
from tower_cli.utils import debug, types, exceptions as exc


class Resource(models.MonitorableResource):
    cli_help = 'Manage inventory sources within Ansible Tower.'
    endpoint = '/inventory_sources/'
    internal = True

    credential = models.Field(type=types.Related('credential'), required=False)
    source = models.Field(
        default='manual',
        help_text='The type of inventory source in use.',
        type=click.Choice(['', 'file', 'ec2', 'rax', 'vmware',
                           'gce', 'azure', 'azure_rm', 'openstack',
                           'satellite6', 'cloudforms', 'custom']),
    )
    source_regions = models.Field(required=False, display=False)
    # Variables not shared by all cloud providers
    source_vars = models.Field(required=False, display=False)
    instance_filters = models.Field(required=False, display=False)
    group_by = models.Field(required=False, display=False)
    source_script = models.Field(type=types.Related('inventory_script'),
                                 required=False)
    # Boolean variables
    overwrite = models.Field(type=bool, required=False, display=False)
    overwrite_vars = models.Field(type=bool, required=False, display=False)
    update_on_launch = models.Field(type=bool, required=False, display=False)
    # Only used if update_on_launch is used
    update_cache_timeout = models.Field(type=int, required=False,
                                        display=False)

    @click.argument('inventory_source', type=types.Related('inventory_source'))
    @click.option('--monitor', is_flag=True, default=False,
                  help='If sent, immediately calls `monitor` on the newly '
                       'launched job rather than exiting with a success.')
    @click.option('--timeout', required=False, type=int,
                  help='If provided with --monitor, this command (not the job)'
                       ' will time out after the given number of seconds. '
                       'Does nothing if --monitor is not sent.')
    @resources.command(use_fields_as_options=False, no_args_is_help=True)
    def update(self, inventory_source, monitor=False, timeout=None, **kwargs):
        """Update the given inventory source."""

        # Establish that we are able to update this inventory source
        # at all.
        debug.log('Asking whether the inventory source can be updated.',
                  header='details')
        r = client.get('%s%d/update/' % (self.endpoint, inventory_source))
        if not r.json()['can_update']:
            raise exc.BadRequest('Tower says it cannot run an update against '
                                 'this inventory source.')

        # Run the update.
        debug.log('Updating the inventory source.', header='details')
        r = client.post('%s%d/update/' % (self.endpoint, inventory_source))

        # If we were told to monitor the project update's status, do so.
        if monitor:
            result = self.monitor(inventory_source, timeout=timeout)
            inventory = client.get('/inventory_sources/%d/' %
                                   result['inventory_source'])\
                              .json()['inventory']
            result['inventory'] = int(inventory)
            return result

        # Done.
        return {'status': 'ok'}

    @resources.command
    @click.option('--detail', is_flag=True, default=False,
                  help='Print more detail.')
    def status(self, pk, detail=False):
        """Print the current job status."""
        # Get the job from Ansible Tower.
        debug.log('Asking for inventory source status.', header='details')
        inv_src = client.get('/inventory_sources/%d/' % pk).json()

        # Determine the appropriate inventory source update.
        if 'current_update' in inv_src['related']:
            debug.log('A current update exists; retrieving it.',
                      header='details')
            job = client.get(inv_src['related']['current_update'][7:]).json()
        elif inv_src['related'].get('last_update', None):
            debug.log('No current update exists; retrieving the most '
                      'recent update.', header='details')
            job = client.get(inv_src['related']['last_update'][7:]).json()
        else:
            raise exc.NotFound('No inventory source updates exist.')

        # In most cases, we probably only want to know the status of the job
        # and the amount of time elapsed. However, if we were asked for
        # verbose information, provide it.
        if detail:
            return job

        # Print just the information we need.
        return {
            'elapsed': job['elapsed'],
            'failed': job['failed'],
            'status': job['status'],
        }
