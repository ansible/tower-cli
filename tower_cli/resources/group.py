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

from tower_cli import get_resource, models, resources
from tower_cli.api import client
from tower_cli.utils import exceptions as exc, types

INVENTORY_SOURCES = ['manual', 'file', 'ec2', 'rax', 'vmware',
                     'gce', 'azure', 'azure_rm', 'openstack',
                     'satellite6', 'cloudforms', 'custom']


class Resource(models.Resource):
    cli_help = 'Manage groups belonging to an inventory.'
    endpoint = '/groups/'
    identity = ('inventory', 'name')

    name = models.Field(unique=True)
    description = models.Field(required=False, display=False)
    inventory = models.Field(type=types.Related('inventory'))
    variables = models.Field(
        type=types.Variables(), required=False, display=False,
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

    # Basic options for the source
    @resources.command
    @click.option('--credential', type=types.Related('credential'),
                  required=False,
                  help='The cloud credential to use.')
    @click.option('--source', type=click.Choice(INVENTORY_SOURCES),
                  default='manual',
                  help='The source to use for this group.')
    @click.option('--source-regions', help='Regions for your cloud provider.')
    # Options may not be valid for certain types of cloud servers
    @click.option('--source-vars', help='Override variables found on source '
                  'with variables defined in this field.')
    @click.option('--instance-filters', help='A comma-separated list of '
                  'filter expressions for matching hosts to be imported to '
                  'Tower.')
    @click.option('--group-by', help='Limit groups automatically created from'
                  ' inventory source.')
    @click.option('--source-script', type=types.Related('inventory_script'),
                  help='Inventory script to be used when group type is '
                  '"custom".')
    @click.option('--overwrite', type=bool,
                  help='Delete child groups and hosts not found in source.')
    @click.option('--overwrite-vars', type=bool,
                  help='Override vars in child groups and hosts with those '
                  'from the external source.')
    @click.option('--update-on-launch', type=bool, help='Refresh inventory '
                  'data from its source each time a job is run.')
    @click.option('--parent',
                  help='Parent group to nest this one inside of.')
    @click.option('--job-timeout', type=int, help='Timeout value (in seconds) '
                  'for underlying inventory source.')
    def create(self, fail_on_found=False, force_on_exists=False, **kwargs):
        """Create a group and, if necessary, modify the inventory source within
        the group.
        """
        group_fields = [f.name for f in self.fields]
        if kwargs.get('parent', None):
            parent_data = self.set_child_endpoint(
                parent=kwargs['parent'],
                inventory=kwargs.get('inventory', None))
            kwargs['inventory'] = parent_data['inventory']
            group_fields.append('group')
        elif 'inventory' not in kwargs:
            raise exc.UsageError('To create a group, you must provide a '
                                 'parent inventory or parent group.')

        # Break out the options for the group vs its inventory_source
        is_kwargs = {}
        for field in kwargs.copy():
            if field not in group_fields:
                if field == 'job_timeout':
                    is_kwargs['timeout'] = kwargs.pop(field)
                else:
                    is_kwargs[field] = kwargs.pop(field)

        # Handle alias for "manual" source
        if is_kwargs.get('source', None) == 'manual':
            is_kwargs.pop('source')

        # First, create the group.
        answer = super(Resource, self).create(
            fail_on_found=fail_on_found, force_on_exists=force_on_exists,
            **kwargs)

        # If the group already exists and we aren't supposed to make changes,
        # then we're done.
        if not force_on_exists and not answer['changed']:
            return answer

        # Sanity check: A group was created, but do we need to do anything
        # with the inventory source at all? If no credential or source
        # was specified, then we'd just be updating the inventory source
        # with an effective no-op.
        if len(is_kwargs) == 0:
            return answer

        # Get the inventory source ID ("isid").
        # Inventory sources are not created directly; rather, one was created
        # automatically when the group was created.
        isid = self._get_inventory_source_id(answer)

        # We now have our inventory source ID; modify it according to the
        # provided parameters.
        isrc = get_resource('inventory_source')
        is_answer = isrc.write(pk=isid, force_on_exists=True, **is_kwargs)

        # If either the inventory_source or the group objects were modified
        # then refelect this in the output to avoid confusing the user.
        if is_answer['changed']:
            answer['changed'] = True
        return answer

    @resources.command
    @click.option('--credential', type=types.Related('credential'),
                  required=False,
                  help='The cloud credential to use.')
    @click.option('--source', type=click.Choice(INVENTORY_SOURCES),
                  help='The source to use for this group.')
    @click.option('--source-regions', help='Regions for your cloud provider.')
    # Options may not be valid for certain types of cloud servers
    @click.option('--source-vars', help='Override variables found on source '
                  'with variables defined in this field.')
    @click.option('--instance-filters', help='A comma-separated list of '
                  'filter expressions for matching hosts to be imported to '
                  'Tower.')
    @click.option('--group-by', help='Limit groups automatically created from'
                  ' inventory source.')
    @click.option('--source-script', type=types.Related('inventory_script'),
                  help='Inventory script to be used when group type is '
                  '"custom".')
    @click.option('--overwrite', type=bool,
                  help='Delete child groups and hosts not found in source.')
    @click.option('--overwrite-vars', type=bool,
                  help='Override vars in child groups and hosts with those '
                  'from the external source.')
    @click.option('--update-on-launch', type=bool, help='Refersh inventory '
                  'data from its source each time a job is run.')
    @click.option('--job-timeout', type=int, help='Timeout value (in seconds) '
                  'for underlying inventory source.')
    def modify(self, pk=None, create_on_missing=False, **kwargs):
        """Modify a group and, if necessary, the inventory source within
        the group.
        """
        # Break out the options for the group vs its inventory_source
        group_fields = [f.name for f in self.fields]
        is_kwargs = {}
        for field in kwargs.copy():
            if field not in group_fields:
                if field == 'job_timeout':
                    is_kwargs['timeout'] = kwargs.pop(field)
                else:
                    is_kwargs[field] = kwargs.pop(field)

        # Handle alias for "manual" source
        if is_kwargs.get('source', None) == 'manual':
            is_kwargs['source'] = ''

        # First, modify the group.
        answer = super(Resource, self).modify(
            pk=pk, create_on_missing=create_on_missing, **kwargs)

        # If the group already exists and we aren't supposed to make changes,
        # then we're done.
        if len(is_kwargs) == 0:
            return answer

        # Get the inventory source ID ("isid").
        # Inventory sources are not created directly; rather, one was created
        # automatically when the group was created.
        isid = self._get_inventory_source_id(answer)

        # We now have our inventory source ID; modify it according to the
        # provided parameters.
        #
        # Note: Any fields that were part of the group modification need
        # to be expunged from kwargs before making this call.
        isrc = get_resource('inventory_source')
        is_answer = isrc.write(pk=isid, force_on_exists=True, **is_kwargs)

        # If either the inventory_source or the group objects were modified
        # then refelect this in the output to avoid confusing the user.
        if is_answer['changed']:
            answer['changed'] = True
        return answer

    @resources.command(ignore_defaults=True, no_args_is_help=False)
    @click.option('--root', is_flag=True, default=False,
                  help='Show only root groups (groups with no parent groups) '
                       'within the given inventory.')
    @click.option('--parent',
                  help='Parent group to nest this one inside of.')
    def list(self, root=False, **kwargs):
        """Return a list of groups."""

        # Option to list children of a parent group
        if kwargs.get('parent', None):
            self.set_child_endpoint(
                parent=kwargs['parent'],
                inventory=kwargs.get('inventory', None)
            )
            kwargs.pop('parent')

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

    @click.argument('group', required=False, type=types.Related('group'))
    @click.option('--monitor', is_flag=True, default=False,
                  help='If sent, immediately calls `monitor` on the newly '
                       'launched job rather than exiting with a success.')
    @click.option('--wait', is_flag=True, default=False,
                  help='Polls server for status, exists when finished.')
    @click.option('--timeout', required=False, type=int,
                  help='If provided with --monitor, this command (not the job)'
                       ' will time out after the given number of seconds. '
                       'Does nothing if --monitor is not sent.')
    @resources.command(no_args_is_help=True)
    def sync(self, group, monitor=False, wait=False, timeout=None, **kwargs):
        """Update the given group's inventory source."""

        isrc = get_resource('inventory_source')
        isid = self._get_inventory_source_id(group, kwargs)
        return isrc.update(isid, monitor=monitor, timeout=timeout,
                           wait=wait, **kwargs)

    @resources.command
    @click.argument('group', required=False, type=types.Related('group'))
    @click.option('--start-line', required=False, type=int,
                  help='Line at which to start printing the standard out.')
    @click.option('--end-line', required=False, type=int,
                  help='Line at which to end printing the standard out.')
    def stdout(self, group, start_line=None, end_line=None, **kwargs):
        """Print the standard out of the last group update."""

        isrc = get_resource('inventory_source')
        isid = self._get_inventory_source_id(group, kwargs)
        return isrc.stdout(isid)

    @resources.command(use_fields_as_options=False)
    @click.option('--group', help='The group to move.')
    @click.option('--parent', help='Destination group to move into.')
    @click.option('--inventory', type=types.Related('inventory'))
    def associate(self, group, parent, **kwargs):
        """Associate this group with the specified group."""
        parent_id = self.lookup_with_inventory(
            parent, kwargs.get('inventory', None))['id']
        group_id = self.lookup_with_inventory(
            group, kwargs.get('inventory', None))['id']
        return self._assoc('children', parent_id, group_id)

    @resources.command(use_fields_as_options=False)
    @click.option('--group', help='The group to move.')
    @click.option('--parent', help='Destination group to move into.')
    @click.option('--inventory', type=types.Related('inventory'))
    def disassociate(self, group, parent, **kwargs):
        """Disassociate this group from the specified group."""
        parent_id = self.lookup_with_inventory(
            parent, kwargs.get('inventory', None))['id']
        group_id = self.lookup_with_inventory(
            group, kwargs.get('inventory', None))['id']
        return self._disassoc('children', parent_id, group_id)

    def _get_inventory_source_id(self, group, data=None):
        """Return the inventory source ID given a group dictionary returned
        from the Tower API. Alternatively, get it from a group's identity
        set in data.
        """
        if group is None:
            group = self.get(**data)
        # If we got a group ID rather than a group, get the group.
        elif isinstance(group, int):
            group = self.get(group)

        # Return the inventory source ID.
        return int(group['related']['inventory_source'].split('/')[-2])
