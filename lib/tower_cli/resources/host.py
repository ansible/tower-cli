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
from tower_cli.utils import types


class Resource(models.Resource):
    cli_help = 'Manage hosts belonging to a group within an inventory.'
    endpoint = '/hosts/'
    identity = ('inventory', 'name')

    name = models.Field(unique=True)
    description = models.Field(required=False, display=False)
    inventory = models.Field(type=types.Related('inventory'))
    enabled = models.Field(type=bool, required=False)
    variables = models.Field(type=types.File('r'), required=False,
                             display=False)

    @resources.command(use_fields_as_options=False)
    @click.option('--host', type=types.Related('host'))
    @click.option('--group', type=types.Related('group'))
    def associate(self, host, group):
        """Associate a group with this host."""
        return self._assoc('groups', host, group)

    @resources.command(use_fields_as_options=False)
    @click.option('--host', type=types.Related('host'))
    @click.option('--group', type=types.Related('group'))
    def disassociate(self, host, group):
        """Disassociate a group from this host."""
        return self._disassoc('groups', host, group)
