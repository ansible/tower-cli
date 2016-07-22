# Copyright 2016, Red Hat
# Alan Rominger <arominge@redhat.com>
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
from tower_cli.utils import types, debug, exceptions as exc


class Resource(models.Resource):
    cli_help = (
        'Manage permissions within Ansible Tower in versions prior to 3.0. \n'
        'Starting with Ansible Tower 3.0, use the role resource to manage '
        'access controls. \n'
        'All commands must specify either a user or a team to operate on.'
    )
    endpoint = '/permissions/'
    identity = ('name', )
    no_lookup_flag = False

    # Permissions must be created for either a user or a team
    name = models.Field(unique=True, required=False, display=True)
    user = models.Field(
        type=types.Related('user'), required=False,
        display=True, help_text='User to grant permission to.')
    team = models.Field(
        type=types.Related('team'), required=False,
        display=True,
        help_text='Team to grant permission to '
                  '(will apply to all members).')

    # Descriptive fields - not in identity or a parent resource
    description = models.Field(required=False, display=False)
    project = models.Field(
        type=types.Related('project'), required=False,
        display=True, help_text='Allows team/user access to this project.')
    inventory = models.Field(
        type=types.Related('inventory'), required=False,
        display=True, help_text='Allows team/user access to this inventory.')
    permission_type = models.Field(
        help_text='The level of access granted.',
        type=click.Choice(
            ["read", "write", "admin", "run", "check", "scan", "create"]))
    run_ad_hoc_commands = models.Field(
        type=bool, required=False, display=False,
        help_text='If "true", includes permission to run ad hoc commands')

    def set_base_url(self, user, team):
        """Assure that endpoint is nested under a user or team"""
        if self.no_lookup_flag:
            return
        if user:
            self.endpoint = '/users/%d/permissions/' % user
        elif team:
            self.endpoint = '/teams/%d/permissions/' % team
        else:
            raise exc.TowerCLIError('Specify either a user or a team.')
        self.no_lookup_flag = True

    def get_permission_pk(self, pk, user, team, **kwargs):
        """Return the pk with a search method specific to permissions."""
        if not pk:
            self.set_base_url(user, team)
            debug.log('Checking for existing permission.', header='details')
            existing_data = self._lookup(
                fail_on_found=False, fail_on_missing=True,
                include_debug_header=False, **kwargs)
            return existing_data['id']
        else:
            self.no_lookup_flag = True
            return pk

    @resources.command
    def create(self, user=None, team=None, **kwargs):
        """Create a permission. Provide one of each:
              Permission granted to: user or team.
              Permission to: inventory or project."""
        self.set_base_url(user, team)
        # Apply default specific to creation
        if not kwargs.get('permission_type', None):
            kwargs['permission_type'] = 'read'
        return super(Resource, self).create(**kwargs)

    @resources.command
    def modify(self, pk=None, user=None, team=None, **kwargs):
        """Modify an already existing permission.

        Provide pk for permission. Alternatively, provide name and the
        parent user/team.

        To modify unique fields, you must use the primary key for the lookup.
        """
        # Use the user-based or team-based endpoint to search for record
        pk = self.get_permission_pk(pk, user, team, **kwargs)
        # Now use the permission-based endpoint to modify the record
        self.endpoint = '/permissions/'
        return super(Resource, self).modify(pk=pk, **kwargs)

    @resources.command
    def delete(self, pk=None, user=None, team=None, **kwargs):
        """Remove the given permission.

        Provide pk for permission. Alternatively, provide name and the
        parent user/team.

        If `fail_on_missing` is True, then the permission's not being found is
        considered a failure; otherwise, a success with no change is reported.
        """
        # Use the user-based or team-based endpoint to search for record
        pk = self.get_permission_pk(pk, user, team, **kwargs)
        # Now use the permission-based endpoint to delete the record
        self.endpoint = '/permissions/'
        return super(Resource, self).delete(pk=pk, **kwargs)

    @resources.command(ignore_defaults=True)
    def get(self, pk=None, user=None, team=None, **kwargs):
        """Return one and exactly one permission.

        Provide pk for permission. Alternatively, provide name and the
        parent user/team.
        """
        self.set_base_url(user, team)
        return super(Resource, self).get(pk=pk, **kwargs)

    @resources.command(ignore_defaults=True, no_args_is_help=False)
    def list(self, user=None, team=None, all_pages=False, **kwargs):
        """Return a list of permissions, specific to given user or team.

        If one or more filters are provided through keyword arguments,
        filter the results accordingly.

        If no filters are provided, return all results. But you still must
        give a user or team because a global listing is not allowed.
        """
        self.set_base_url(user, team)
        return super(Resource, self).list(all_pages=all_pages, **kwargs)
