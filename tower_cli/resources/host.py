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


class Resource(models.Resource):
    """A resource for credentials."""
    cli_help = 'Manage hosts belonging to a group within an inventory.'
    endpoint = '/hosts/'
    identity = ('inventory', 'name')

    name = models.Field(unique=True)
    description = models.Field(required=False, display=False)
    inventory = models.Field(type=types.Related('inventory'))
    enabled = models.Field(type=bool, required=False)
    variables = models.Field(
        type=types.Variables(), required=False, display=False,
        help_text='Host variables, use "@" to get from file.')

    @resources.command(use_fields_as_options=False)
    @click.option('--host', type=types.Related('host'))
    @click.option('--group', type=types.Related('group'))
    def associate(self, host, group):
        """Associate a group with this host.

        =====API DOCS=====
        Associate a group with this host.

        :param host: Primary key or name of the host to be associated.
        :type host: str
        :param group: Primary key or name of the group to associate.
        :type group: str
        :returns: Dictionary of only one key "changed", which indicates whether the association succeeded.
        :rtype: dict

        =====API DOCS=====
        """
        return self._assoc('groups', host, group)

    @resources.command(use_fields_as_options=False)
    @click.option('--host', type=types.Related('host'))
    @click.option('--group', type=types.Related('group'))
    def disassociate(self, host, group):
        """Disassociate a group from this host.

        =====API DOCS=====
        Disassociate a group from this host.

        :param host: Primary key or name of the host to be disassociated.
        :type host: str
        :param group: Primary key or name of the group to disassociate.
        :type group: str
        :returns: Dictionary of only one key "changed", which indicates whether the disassociation succeeded.
        :rtype: dict

        =====API DOCS=====
        """
        return self._disassoc('groups', host, group)

    @resources.command(ignore_defaults=True, no_args_is_help=False)
    @click.option('--group', type=types.Related('group'),
                  help='List hosts that are children of this group.')
    def list(self, group=None, **kwargs):
        """Return a list of hosts.

        =====API DOCS=====
        Retrieve a list of hosts.

        :param group: Primary key or name of the group whose hosts will be listed.
        :type group: str
        :param all_pages: Flag that if set, collect all pages of content from the API when returning results.
        :type all_pages: bool
        :param page: The page to show. Ignored if all_pages is set.
        :type page: int
        :param query: Contains 2-tuples used as query parameters to filter resulting resource objects.
        :type query: list
        :param `**kwargs`: Keyword arguments list of available fields used for searching resource objects.
        :returns: A JSON object containing details of all resource objects returned by Tower backend.
        :rtype: dict

        =====API DOCS=====
        """
        if group:
            kwargs['query'] = (kwargs.get('query', ()) +
                               (('groups__in', group),))
        return super(Resource, self).list(**kwargs)
