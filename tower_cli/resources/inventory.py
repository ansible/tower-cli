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
    dependencies = ['organization']
    related = ['host', 'group', 'inventory_source']

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

    instance_groups = models.ManyToManyField('instance_group', method_name='ig')

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
