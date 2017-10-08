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

from tower_cli import get_resource, models, resources, exceptions as exc
from tower_cli.api import client
from tower_cli.cli import types


class Resource(models.Resource):
    """A resource for groups."""
    cli_help = 'Manage groups belonging to an inventory.'
    endpoint = '/groups/'
    identity = ('inventory', 'name')

    name = models.Field(unique=True)
    description = models.Field(required=False, display=False)
    inventory = models.Field(type=types.Related('inventory'))
    variables = models.Field(type=types.Variables(), required=False, display=False,
                             help_text='Group variables, use "@" to get from file.')

    def lookup_with_inventory(self, group, inventory=None):
        group_res = get_resource('group')
        if isinstance(group, int) or group.isdigit():
            return group_res.get(int(group))
        else:
            return group_res.get(name=group, inventory=inventory)

    def set_child_endpoint(self, parent, inventory=None):
        parent_data = self.lookup_with_inventory(parent, inventory)
        self.endpoint = '/groups/' + str(parent_data['id']) + '/children/'
        return parent_data

    @resources.command
    @click.option('--parent', help='Parent group to nest this one inside of.')
    def create(self, fail_on_found=False, force_on_exists=False, **kwargs):
        """Create a group.

        =====API DOCS=====
        Create a group.

        :param parent: Primary key or name of the group which will be the parent of created group.
        :type parent: str
        :param fail_on_found: Flag that if set, the operation fails if an object matching the unique criteria
                              already exists.
        :type fail_on_found: bool
        :param force_on_exists: Flag that if set, then if a match is found on unique fields, other fields will
                                be updated to the provided values.; If unset, a match causes the request to be
                                a no-op.
        :type force_on_exists: bool
        :param `**kwargs`: Keyword arguments which, all together, will be used as POST body to create the
                           resource object.
        :returns: A dictionary combining the JSON output of the created resource, as well as two extra fields:
                  "changed", a flag indicating if the resource is created successfully; "id", an integer which
                  is the primary key of the created object.
        :rtype: dict
        :raises tower_cli.exceptions.UsageError: When inventory is not provided in ``**kwargs`` and ``parent``
                                                 is not provided.

        =====API DOCS=====
        """
        if kwargs.get('parent', None):
            parent_data = self.set_child_endpoint(parent=kwargs['parent'], inventory=kwargs.get('inventory', None))
            kwargs['inventory'] = parent_data['inventory']
        elif 'inventory' not in kwargs:
            raise exc.UsageError('To create a group, you must provide a parent inventory or parent group.')
        return super(Resource, self).create(fail_on_found=fail_on_found, force_on_exists=force_on_exists, **kwargs)

    @resources.command(ignore_defaults=True, no_args_is_help=False)
    @click.option('--root', is_flag=True, default=False,
                  help='Show only root groups (groups with no parent groups) within the given inventory.')
    @click.option('--parent', help='Parent group to nest this one inside of.')
    def list(self, root=False, **kwargs):
        """Return a list of groups.

        =====API DOCS=====
        Retrieve a list of groups.

        :param root: Flag that if set, only root groups of a specific inventory will be listed.
        :type root: bool
        :param parent: Primary key or name of the group whose child groups will be listed.
        :type parent: str
        :param all_pages: Flag that if set, collect all pages of content from the API when returning results.
        :type all_pages: bool
        :param page: The page to show. Ignored if all_pages is set.
        :type page: int
        :param query: Contains 2-tuples used as query parameters to filter resulting resource objects.
        :type query: list
        :param `**kwargs`: Keyword arguments list of available fields used for searching resource objects.
        :returns: A JSON object containing details of all resource objects returned by Tower backend.
        :rtype: dict
        :raises tower_cli.exceptions.UsageError: When ``root`` flag is on and ``inventory`` is not present in
                                                 ``**kwargs``.

        =====API DOCS=====
        """
        # Option to list children of a parent group
        if kwargs.get('parent', None):
            self.set_child_endpoint(parent=kwargs['parent'], inventory=kwargs.get('inventory', None))
            kwargs.pop('parent')
        # Sanity check: If we got `--root` and no inventory, that's an error.
        if root and not kwargs.get('inventory', None):
            raise exc.UsageError('The --root option requires specifying an inventory also.')
        # If we are tasked with getting root groups, do that.
        if root:
            inventory_id = kwargs['inventory']
            r = client.get('/inventories/%d/root_groups/' % inventory_id)
            return r.json()
        # Return the superclass implementation.
        return super(Resource, self).list(**kwargs)

    @resources.command(use_fields_as_options=False)
    @click.option('--group', help='The group to move.')
    @click.option('--parent', help='Destination group to move into.')
    @click.option('--inventory', type=types.Related('inventory'))
    def associate(self, group, parent, **kwargs):
        """Associate this group with the specified group.

        =====API DOCS=====
        Associate this group with the specified group.

        :param group: Primary key or name of the child group to associate.
        :type group: str
        :param parent: Primary key or name of the parent group to associate to.
        :type parent: str
        :param inventory: Primary key or name of the inventory the association should happen in.
        :type inventory: str
        :returns: Dictionary of only one key "changed", which indicates whether the association succeeded.
        :rtype: dict

        =====API DOCS=====
        """
        parent_id = self.lookup_with_inventory(parent, kwargs.get('inventory', None))['id']
        group_id = self.lookup_with_inventory(group, kwargs.get('inventory', None))['id']
        return self._assoc('children', parent_id, group_id)

    @resources.command(use_fields_as_options=False)
    @click.option('--group', help='The group to move.')
    @click.option('--parent', help='Destination group to move into.')
    @click.option('--inventory', type=types.Related('inventory'))
    def disassociate(self, group, parent, **kwargs):
        """Disassociate this group from the specified group.

        =====API DOCS=====
        Disassociate this group with the specified group.

        :param group: Primary key or name of the child group to disassociate.
        :type group: str
        :param parent: Primary key or name of the parent group to disassociate from.
        :type parent: str
        :param inventory: Primary key or name of the inventory the disassociation should happen in.
        :type inventory: str
        :returns: Dictionary of only one key "changed", which indicates whether the disassociation succeeded.
        :rtype: dict

        =====API DOCS=====
        """
        parent_id = self.lookup_with_inventory(parent, kwargs.get('inventory', None))['id']
        group_id = self.lookup_with_inventory(group, kwargs.get('inventory', None))['id']
        return self._disassoc('children', parent_id, group_id)
