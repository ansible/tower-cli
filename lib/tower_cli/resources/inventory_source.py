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
    internal = True

    credential = models.Field(type=types.Related('credential'), required=False)
    source = models.Field(
        default='manual',
        help_text='The type of inventory source in use.',
        type=click.Choice(['manual', 'ec2', 'rax', 'gce', 'azure']),
    )

    @click.argument('inventory_source', type=types.Related('inventory_source'))
    @resources.command(use_fields_as_options=False, no_args_is_help=True)
    def sync(self, inventory_source, **kwargs):
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
