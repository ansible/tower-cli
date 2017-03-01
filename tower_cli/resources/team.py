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
    cli_help = 'Manage teams within Ansible Tower.'
    endpoint = '/teams/'
    identity = ('organization', 'name')

    name = models.Field(unique=True)
    organization = models.Field(type=types.Related('organization'))
    description = models.Field(required=False, display=False)

    @resources.command(use_fields_as_options=False)
    @click.option('--team', type=types.Related('team'))
    @click.option('--user', type=types.Related('user'))
    def associate(self, team, user):
        """Associate a user with this team."""
        return self._assoc('users', team, user)

    @resources.command(use_fields_as_options=False)
    @click.option('--team', type=types.Related('team'))
    @click.option('--user', type=types.Related('user'))
    def disassociate(self, team, user):
        """Disassociate a user from this team."""
        return self._disassoc('users', team, user)
