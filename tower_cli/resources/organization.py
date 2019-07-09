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
    cli_help = 'Manage organizations within Ansible Tower.'
    endpoint = '/organizations/'
    deprecated_methods = ['associate_project', 'disassociate_project']

    name = models.Field(unique=True)
    description = models.Field(required=False, display=False)
    users = models.ManyToManyField('user', method_name='')
    admins = models.ManyToManyField('user', method_name='admin')
    instance_groups = models.ManyToManyField('instance_group', method_name='ig')
    custom_virtualenv = models.Field(required=False, display=False)

    @resources.command(use_fields_as_options=False)
    @click.option('--organization', type=types.Related('organization'))
    @click.option('--notification-template',
                  type=types.Related('notification_template'))
    @click.option('--status', type=click.Choice(['any', 'error', 'success']),
                  required=False, default='any', help='Specify job run status'
                  ' of inventory_sync to relate to.')
    def associate_notification_template(self, organization,
                                        notification_template, status):
        """Associate a notification template from this organization.

        =====API DOCS=====
        Associate a notification template from this organization.

        :param organization: The organization to associate to.
        :type organization: str
        :param notification_template: The notification template to be associated.
        :type notification_template: str
        :param status: type of notification this notification template should be associated to.
        :type status: str
        :returns: Dictionary of only one key "changed", which indicates whether the association succeeded.
        :rtype: dict

        =====API DOCS=====
        """
        return self._assoc('notification_templates_%s' % status,
                           organization, notification_template)

    @resources.command(use_fields_as_options=False)
    @click.option('--organization', type=types.Related('organization'))
    @click.option('--notification-template',
                  type=types.Related('notification_template'))
    @click.option('--status', type=click.Choice(['any', 'error', 'success']),
                  required=False, default='any', help='Specify job run status'
                  ' of inventory_sync to relate to.')
    def disassociate_notification_template(self, organization,
                                           notification_template, status):
        """Disassociate a notification template from this organization.

        =====API DOCS=====
        Disassociate a notification template from this organization.

        :param organization: The organization to disassociate from.
        :type organization: str
        :param notification_template: The notification template to be disassociated.
        :type notification_template: str
        :param status: type of notification this notification template should be disassociated from.
        :type status: str
        :returns: Dictionary of only one key "changed", which indicates whether the disassociation succeeded.
        :rtype: dict

        =====API DOCS=====
        """
        return self._disassoc('notification_templates_%s' % status,
                              organization, notification_template)
