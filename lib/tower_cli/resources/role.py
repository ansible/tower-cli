# Copyright 2016, Ansible by Red Hat
# Alan Rominger <arominge@redhat.com>
# Aaron Tan
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
from tower_cli.utils import (
    debug,
    types,
    exceptions as exc
)
from tower_cli.conf import settings

from copy import copy


RESOURCE_FIELDS = [
    'user', 'team', 'credential', 'inventory', 'job_template', 'credential',
    'organization', 'project', 'type'
]

ROLE_TYPES = [
    'admin', 'read', 'member', 'owner', 'execute', 'adhoc', 'update',
    'use', 'auditor'
]


class Resource(models.ResourceMethods):
    """A resource for managing roles.

    This resource has ordinary list and get methods,
    but it roles can not be created or edited, instead, they are
    automatically generated along with the connected resource.
    """
    cli_help = 'Add and remove users/teams from roles.'
    endpoint = '/roles/'

    user = models.Field(type=types.Related('user'), required=False, display=True)
    team = models.Field(type=types.Related('team'), required=False, display=True)
    type = models.Field(
        required=False, display=True, type=click.Choice(ROLE_TYPES),
        help_text='The type of permission that the role controls.')

    # These fields are never valid input arguments,
    # they are only used as columns in output
    resource_name = models.Field(required=False, display=False)
    resource_type = models.Field(required=False, display=False)

    # These are purely resource fields, and are always inputs,
    # but are only selectively set as output columns
    credential = models.Field(type=types.Related('credential'), required=False, display=False)
    inventory = models.Field(type=types.Related('inventory'), required=False, display=False)
    job_template = models.Field(type=types.Related('job_template'), required=False, display=False)
    credential = models.Field(type=types.Related('credential'), required=False, display=False)
    organization = models.Field(type=types.Related('organization'), required=False, display=False)
    project = models.Field(type=types.Related('project'), required=False, display=False)

    def __getattribute__(self, name):
        """Disable inherited methods that cannot be applied to this
        particular resource.
        """
        if name in ['create', 'delete', 'modify']:
            raise AttributeError
        else:
            return object.__getattribute__(self, name)

    @staticmethod
    def pluralize(kind):
        if kind == 'inventory':
            return 'inventories'
        else:
            return '%ss' % kind

    def field_names(self):
        name_list = []
        for fd in self.fields:
            name_list.append(fd.name)
        return name_list

    def obj_subobj(self, data, fail_on=['type', 'obj', 'res']):
        """Processes input data, returns the following and their types:
        obj - the role grantee
        res - the resource that the role applies to"""
        errors = ''
        if not data.get('type', None) and 'type' in fail_on:
            errors = 'You must provide a role type to use this command.'

        # Find the grantee, and remove them from resource_list
        resource_list = copy(data)
        if data.get('user', False):
            obj = resource_list.pop('user')
            obj_type = 'user'
        elif data.get('team', False):
            obj = resource_list.pop('team')
            obj_type = 'team'
        elif 'obj' in fail_on:
            errors = '\n'.join([errors, 'You must specify either user or team to use this command.'])
            obj = None
            obj_type = None

        # Out of the resource list, pick out available valid resource field
        res = None
        res_type = None
        field_list = self.field_names()
        for fd in resource_list:
            if fd not in field_list:
                continue
            if resource_list[fd] is not None and fd != 'type':
                res = resource_list[fd]
                res_type = fd
        if not res and 'res' in fail_on:
            errors = '\n'.join([errors, 'You must specify a target resource to use this command.'])

        if errors and throw_errors:
            raise exc.UsageError(errors)
        return obj, obj_type, res, res_type

    def read_role(self, res, res_type, type, fail_on_no_results=True):
        """Re-implementation of the parent `read` method specific to roles."""
        # TODO: deprecate this method and integrate with the parent class
        res_plural = self.pluralize(res_type)
        role_search_url = '%s/%s/object_roles/' % (res_plural, res)
        debug.log('Getting role information.', header='details')
        r = client.get(role_search_url, params={'role_field': '%s_role' % type})
        resp = r.json()
        if fail_on_no_results and resp['count'] == 0:
            raise exc.NotFound('The role could not be found.')
        return resp

    def set_display(self, set_true=[], set_false=[]):
        """Add or remove columns from the output."""
        for i in range(len(self.fields)):
            if self.fields[i].name in set_true:
                self.fields[i].display = True
            elif self.fields[i].name in set_false:
                self.fields[i].display = False

    def role_write(self, fail_on_found=False, disassociate=False, **kwargs):
        """Re-implementation of the parent `write` method specific to roles.
        Adds a grantee (user or team) to the resource's role."""

        # Parse the input data, determine which is resource and which
        obj, obj_type, res, res_type = self.obj_subobj(kwargs)

        # Get the role
        role_data = self.read_role(res, res_type, kwargs['type'])
        response = role_data['results'][0]
        role_id = response['id']

        # Role exists, change display settings to reflect this
        if settings.format == 'human':
            response['type'] = kwargs['type']
            if obj_type == 'user':
                self.set_display(set_false=['team'], set_true=[res_type])
                response['user'] = obj
                response[res_type] = res
            else:
                self.set_display(set_false=['user'], set_true=[res_type])
                response['team'] = obj
                response[res_type] = res

        # Check if user/team has this role
        # Implictly, force_on_exists is false for roles
        debug.log('Checking if %s already has role.' % obj_type, header='details')
        r = client.get('%s/%s/roles' % (self.pluralize(obj_type), obj),
                       params={'id': role_id})
        resp = r.json()
        if (resp['count'] > 0 and not disassociate) or (resp['count'] == 0 and disassociate):
            response['changed'] = False
            if fail_on_found:
                raise exc.NotFound('This %s is already a member of this role.' % obj_type)
            else:
                return response

        # Add or remove the user/team to the role
        if disassociate:
            debug.log('Attempting to remove the %s from this role.' % obj_type, header='details')
        else:
            debug.log('Attempting to add the %s to this role.' % obj_type, header='details')
        post_data = {'id': role_id}
        if disassociate:
            post_data['disassociate'] = True
        r = client.post('%s/%s/roles/' % (self.pluralize(obj_type), obj),
                        data=post_data)

        response['changed'] = True
        return response

    def set_resource_endpoint(self, data):
        """Removes the resource field from `data` and sets the endpoint to
        the roles subendpoint for that resource.

        Also changes the format of `type` in data to what the server
        expects for the role model, as it exists in the database."""
        obj, obj_type, res, res_type = self.obj_subobj(data, throw_errors=False)
        # Input fields are not actually present on role model, and all have
        # to be managed as individual special-cases
        if obj and obj_type == 'user':
            data['members__in'] = obj
        if obj and obj_type == 'team':
            self.endpoint = '%s/%s/roles/' % (self.pluralize(obj_type), obj)
            data[obj_type] = None
            if res is not None:
                # For teams, this is the best lookup we can do
                #  without making the addional request for its member_role
                data['content_id'] = res
        elif res:
            self.endpoint = '%s/%s/object_roles/' % (self.pluralize(res_type), res)
            data[res_type] = None
        if data.get('type', False):
            data['role_field'] = '%s_role' % data['type'].lower()
            data['type'] = None
        # TODO: add members__in to querystring for user
        # TODO: GET team member_role, add querystring filter parent

    @staticmethod
    def populate_resource_columns(item_dict):
        """Operates on item_dict

        Promotes the resource_name and resource_type fields to the
        top-level of the serialization so they can be printed as columns.
        Also makes a copies name field to type, which is a default column."""
        item_dict['type'] = item_dict['name']
        if len(item_dict['summary_fields']) == 0:
            # Singleton roles ommit these fields
            item_dict['resource_name'] = None
            item_dict['resource_type'] = None
        else:
            item_dict['resource_name'] = item_dict['summary_fields']['resource_name']
            item_dict['resource_type'] = item_dict['summary_fields']['resource_type']

    # Command method for roles
    # TODO: write commands to see access_list for resource
    @resources.command(use_fields_as_options=RESOURCE_FIELDS)
    def list(self, **kwargs):
        """Return a list of roles."""
        obj, obj_type, res, res_type = self.obj_subobj(data, throw_errors=False)
        data = self.set_resource_endpoint(obj, obj_type, res, res_type)
        r = super(Resource, self).list(**data)

        # Change display settings and data format for human consumption
        if settings.format == 'human':
            self.set_display(set_false=['user', 'team'], set_true=['resource_name', 'resource_type'])
            for i in range(len(r['results'])):
                self.populate_resource_columns(r['results'][i])
        return r

    @resources.command(use_fields_as_options=RESOURCE_FIELDS)
    def get(self, pk=None, **kwargs):
        """Get information about a role."""
        self.set_resource_endpoint(kwargs)
        if kwargs.pop('include_debug_header', True):
            debug.log('Getting the role record.', header='details')
        response = self.read(pk=pk, fail_on_no_results=True,
                             fail_on_multiple_results=True, **kwargs)
        item_dict = response['results'][0]
        if settings.format == 'human':
            self.set_display(set_false=['user', 'team'], set_true=['resource_name', 'resource_type'])
            self.populate_resource_columns(item_dict)
        return item_dict

    @resources.command(use_fields_as_options=RESOURCE_FIELDS)
    @click.option('--fail-on-found', default=False,
                  show_default=True, type=bool, is_flag=True,
                  help='If used, return an error if the user already has the '
                       'role.')
    def grant(self, fail_on_found=False, **kwargs):
        """Add a user or a team to a role.

        Required information:
        1) Type of the role
        2) Resource of the role, inventory, credential, or any other
        3) A user or a team to add to the role"""
        return self.role_write(fail_on_found, **kwargs)

    @resources.command(use_fields_as_options=RESOURCE_FIELDS)
    @click.option('--fail-on-found', default=False,
                  show_default=True, type=bool, is_flag=True,
                  help='If used, return an error if the user is already '
                       'not a member of the role.')
    def revoke(self, fail_on_found=False, **kwargs):
        """Remove a user or a team from a role.

        Required information:
        1) Type of the role
        2) Resource of the role, inventory, credential, or any other
        3) A user or a team to add to the role"""
        return self.role_write(fail_on_found, disassociate=True, **kwargs)
