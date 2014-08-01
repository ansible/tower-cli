# Copyright 2014, Ansible, Inc.
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

import tower_cli
from tower_cli import models, resources
from tower_cli.api import client
from tower_cli.utils import types, exceptions as exc


class Resource(models.Resource):
    cli_help = 'Manage inventory sources within Ansible Tower.'
    endpoint = '/inventory_sources/'

    credential = models.Field(type=types.Related('credential'), required=False)
    source = models.Field(
        default='manual',
        help_text='The type of inventory source in use.',
        type=click.Choice(['manual', 'ec2', 'rax', 'gce', 'azure']),
    )    

    @click.option('--name', help='The name field.')
    @click.option('--inventory', type=types.Related('inventory'))
    def create(self, name=None, inventory=None, credential=None,
                     source=None, **kwargs):
        """Create a group and inventory source within the
        given inventory.
        """
        # Inventory sources are not created directly; rather, we create
        # a group, which will automatically create an inventory source.
        # Then, we'll modify the inventory source appropriately.
        group_resource = tower_cli.get_resource('group')        
        group = group_resource.create(name=name, inventory=inventory, **kwargs)
        isource_id = int(group['related']['inventory_source'].split('/')[-2])

        # If the group already exists and we aren't supposed to make changes,
        # then abort now, but send back the inventory source.
        if not kwargs.pop('force_on_exists', False) and not group['changed']:
            answer = self.get(isource_id)
            answer['changed'] = False
            return answer

        # We now have our inventory source ID; modify it according to the
        # provided parameters.
        return self.modify(isource_id, credential=credential, source=source,
                                       force_on_exists=True, **kwargs)

    @click.argument('inventory_source', type=types.Related('inventory_source'))
    @resources.command(use_fields_as_options=False, no_args_is_help=True)
    def update(self, inventory_source, **kwargs):
        """Update the given inventory source."""

        # Establish that we are able to update this inventory source
        # at all.
        r = client.get('%s%d/update/' % (self.endpoint, inventory_source))
        if not r.json()['can_update']:
            raise exc.BadRequest('Tower says it cannot run an update against '
                                 'this inventory source.')

        # Run the update.
        r = client.post('%s%d/update/' % (self.endpoint, inventory_source))
        return {'status': 'ok'}
