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
    """A resource for credentials."""
    cli_help = 'Manage hosts belonging to a group within an inventory.'
    endpoint = '/hosts/'
    identity = ('inventory', 'name')

    name = models.Field(unique=True)
    description = models.Field(required=False, display=False)
    inventory = models.Field(type=types.Related('inventory'))
    enabled = models.Field(type=bool, required=False)
    variables = models.Field(type=types.Variables(), required=False, display=False,
                             help_text='Host variables, use "@" to get from file.')
    insights_system_id = models.Field(required=False, display=False)

    groups = models.ManyToManyField('group', method_name='')

    @resources.command(ignore_defaults=True, no_args_is_help=False)
    @click.option('--group', type=types.Related('group'), help='List hosts that are children of this group.')
    @click.option('--host-filter', help='List hosts filtered by this fact search query string.')
    def list(self, group=None, host_filter=None, **kwargs):
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
            kwargs['query'] = kwargs.get('query', ()) + (('groups__in', group),)
        if host_filter:
            kwargs['query'] = kwargs.get('query', ()) + (('host_filter', host_filter),)
        return super(Resource, self).list(**kwargs)

    @resources.command(ignore_defaults=True)
    def list_facts(self, pk=None, **kwargs):
        """Return a JSON object of all available facts of the given host.

        Note global option --format is not available here, as the output would always be JSON-formatted.

        =====API DOCS=====
        List all available facts of the given host.

        :param pk: Primary key of the target host.
        :type pk: int
        :param `**kwargs`: Keyword arguments list of available fields used for searching resource objects.
        :returns: A JSON object of all available facts of the given host.
        :rtype: dict
        =====API DOCS=====
        """
        res = self.get(pk=pk, **kwargs)
        url = self.endpoint + '%d/%s/' % (res['id'], 'ansible_facts')
        return client.get(url, params={}).json()

    list_facts.format_freezer = 'json'

    @resources.command(ignore_defaults=True)
    def insights(self, pk=None, **kwargs):
        """Return a JSON object of host insights.

        Note global option --format is not available here, as the output would always be JSON-formatted.

        =====API DOCS=====
        List host insights.

        :param pk: Primary key of the target host.
        :type pk: int
        :param `**kwargs`: Keyword arguments list of available fields used for searching resource objects.
        :returns: A JSON object of host insights.
        :rtype: dict
        =====API DOCS=====
        """
        res = self.get(pk=pk, **kwargs)
        url = self.endpoint + '%d/%s/' % (res['id'], 'insights')
        return client.get(url, params={}).json()

    insights.format_freezer = 'json'
