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

from tower_cli import models, resources
from tower_cli.api import client
from tower_cli.utils import exceptions as exc, types


class Resource(models.Resource):
    cli_help = 'Manage groups belonging to an inventory.'
    endpoint = '/groups/'

    name = models.Field(unique=True)
    description = models.Field(required=False, display=False)
    inventory = models.Field(type=types.Related('inventory'))
    variables = models.Field(type=types.File('r'), required=False,
                             display=False)

    @resources.command(ignore_defaults=True, no_args_is_help=False)
    @click.option('--root', is_flag=True, default=False,
                  help='Show only root groups (groups with no parent groups) '
                       'within the given inventory.')
    def list(self, root=False, **kwargs):
        """Return a list of groups."""

        # Sanity check: If we got `--root` and no inventory, that's an
        # error.
        if root and not kwargs.get('inventory', None):
            raise exc.UsageError('The --root option requires specifying an '
                                 'inventory also.')

        # If we are tasked with getting root groups, do that.
        if root:
            inventory_id = kwargs['inventory']
            r = client.get('/inventories/%d/root_groups/' % inventory_id)
            return r.json()

        # Return the superclass implementation.
        return super(Resource, self).list(**kwargs)
