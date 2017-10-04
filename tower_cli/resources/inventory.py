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
from tower_cli.cli import types
from tower_cli.api import client


class Resource(models.Resource):
    """A resource for inventories."""
    cli_help = 'Manage inventory within Ansible Tower.'
    endpoint = '/inventories/'
    identity = ('organization', 'name')

    name = models.Field(unique=True)
    description = models.Field(required=False, display=False)
    organization = models.Field(type=types.Related('organization'))
    variables = models.Field(type=types.Variables(), required=False, display=False,
                             help_text='Inventory variables, use "@" to get from file.')
    kind = models.Field(type=click.Choice(['', 'smart']), required=False, display=False,
                        help_text='The kind field. Cannot be modified after created.')
    host_filter = models.Field(required=False, display=False,
                               help_text='The host_filter field. Only useful when kind=smart.')
    insights_credential = models.Field(display=False, required=False, type=types.Related('credential'))

    @resources.command(ignore_defaults=True)
    def batch_update(self, pk=None, **kwargs):
        """Update all related inventory sources of the given inventory.

        Note global option --format is not available here, as the output would always be JSON-formatted.

        =====API DOCS=====
        Update all related inventory sources of the given inventory.

        :param pk: Primary key of the given inventory.
        :type pk: int
        :param `**kwargs`: Keyword arguments list of available fields used for searching resource objects.
        :returns: A JSON object of update status of the given inventory.
        :rtype: dict
        =====API DOCS=====
        """
        res = self.get(pk=pk, **kwargs)
        url = self.endpoint + '%d/%s/' % (res['id'], 'update_inventory_sources')
        return client.post(url, data={}).json()

    batch_update.format_freezer = 'json'

    @resources.command(use_fields_as_options=False)
    @click.option('--inventory', type=types.Related('inventory'), required=True)
    @click.option('--instance-group', type=types.Related('instance_group'), required=True)
    def associate_ig(self, inventory, instance_group):
        """Associate an instance group with this inventory.
        The instance group will be used to run jobs within the inventory.

        =====API DOCS=====
        Associate an instance group with this inventory.

        :param inventory: Primary key or name of the inventory to associate to.
        :type inventory: str
        :param instance_group: Primary key or name of the instance group to be associated.
        :type instance_group: str
        :returns: Dictionary of only one key "changed", which indicates whether the association succeeded.
        :rtype: dict

        =====API DOCS=====
        """
        return self._assoc('instance_groups', inventory, instance_group)

    @resources.command(use_fields_as_options=False)
    @click.option('--inventory', type=types.Related('inventory'), required=True)
    @click.option('--instance-group', type=types.Related('instance_group'), required=True)
    def disassociate_ig(self, inventory, instance_group):
        """Disassociate an instance group from this inventory.

        =====API DOCS=====
        Disassociate an instance group with this inventory.

        :param inventory: Primary key or name of the inventory to associate to.
        :type inventory: str
        :param instance_group: Primary key or name of the instance group to be associated.
        :type instance_group: str
        :returns: Dictionary of only one key "changed", which indicates whether the association succeeded.
        :rtype: dict

        =====API DOCS=====
        """
        return self._disassoc('instance_groups', inventory, instance_group)
