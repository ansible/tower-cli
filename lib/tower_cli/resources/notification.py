# Copyright 2016, Ansible, Inc.
# Aaron Tan <sitan@redhat.com>
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
import json
import copy

from tower_cli import models, resources
from tower_cli.utils import types, debug, exceptions as exc


class Resource(models.Resource):
    cli_help = 'Manage notifications within Ansible Tower.'
    endpoint = '/notification_templates/'

    # Actual fields
    name = models.Field(unique=True)
    description = models.Field(required=False, display=False)
    organization = models.Field(type=types.Related('organization'),
                                required=False, display=False)
    notification_type = models.Field(
        type=click.Choice(['email', 'slack', 'twilio', 'pagerduty',
                           'hipchat', 'webhook', 'irc'])
    )
    notification_configuration = models.Field(
        type=models.File('r', lazy=True), required=False, display=False,
        help_text='The notification configuration field. Note providing this'
                  ' field would disable all notification-configuration-related'
                  ' fields.'
    )

    # Fields that are part of notification_configuration
    config_fields = ['notification_configuration', 'channels', 'token',
                     'username', 'sender', 'recipients', 'use_tls',
                     'host', 'use_ssl', 'password', 'port', 'account_token',
                     'from_number', 'to_numbers', 'account_sid', 'subdomain',
                     'service_key', 'client_name', 'message_from', 'api_url',
                     'color', 'notify', 'rooms', 'url', 'headers', 'server',
                     'nickname', 'targets']
    # Fields that are part of notification_configuration which are categorized
    # according to notification_type
    configuration = {
        'slack': ['channels', 'token'],
        'email': ['username', 'sender', 'recipients', 'use_tls', 'host',
                  'use_ssl', 'password', 'port'],
        'twilio': ['account_token', 'from_number', 'to_numbers',
                   'account_sid'],
        'pagerduty': ['token', 'subdomain', 'service_key', 'client_name'],
        'hipchat': ['message_from', 'api_url', 'color', 'token', 'notify',
                    'rooms'],
        'webhook': ['url', 'headers'],
        'irc': ['server', 'port', 'use_ssl', 'password', 'nickname', 'targets']
    }

    # Fields which are expected to be json files.
    json_fields = ['notification_configuration', 'headers']

    # notification_configuration-related fields. fields with default values
    # are optional.
    username = models.Field(required=False, display=False,
                            help_text='[{}]The username.'.format('email'))
    sender = models.Field(required=False, display=False,
                          help_text='[{}]The sender.'.format('email'))
    recipients = models.Field(required=False, display=False, multiple=True,
                              help_text='[{}]The recipients.'.format('email'))
    use_tls = models.Field(required=False, display=False, type=click.BOOL,
                           default=False,
                           help_text='[{}]The tls trigger.'.format('email'))
    host = models.Field(required=False, display=False,
                        help_text='[{}]The host.'.format('email'))
    use_ssl = models.Field(required=False, display=False, type=click.BOOL,
                           default=False, help_text='[{}]The ssl trigger.'
                           .format('email/irc'))
    password = models.Field(required=False, display=False, password=True,
                            help_text='[{}]The password.'.format('email/irc'))
    port = models.Field(required=False, display=False, type=click.INT,
                        help_text='[{}]The email port.'.format('email/irc'))
    channels = models.Field(required=False, display=False, multiple=True,
                            help_text='[{}]The channel.'.format('slack'))
    token = models.Field(required=False, display=False, password=True,
                         help_text='[{}]The token.'.
                         format('slack/pagerduty/hipchat'))
    account_token = models.Field(required=False, display=False, password=True,
                                 help_text='[{}]The account token.'.
                                 format('twilio'))
    from_number = models.Field(required=False, display=False,
                               help_text='[{}]The source phone number.'.
                               format('twilio'))
    to_numbers = models.Field(required=False, display=False, multiple=True,
                              help_text='[{}]The destination SMS numbers.'.
                              format('twilio'))
    account_sid = models.Field(required=False, display=False,
                               help_text='[{}The account sid.'.
                               format('twilio'))
    subdomain = models.Field(required=False, display=False,
                             help_text='[{}]The subdomain.'.
                             format('pagerduty'))
    service_key = models.Field(required=False, display=False,
                               help_text='[{}]The API service/integration'
                               ' key.'.format('pagerduty'))
    client_name = models.Field(required=False, display=False,
                               help_text='[{}]The client identifier.'.
                               format('pagerduty'))
    message_from = models.Field(required=False, display=False,
                                help_text='[{}]The label to be shown with '
                                'notification.'.format('hipchat'))
    api_url = models.Field(required=False, display=False,
                           help_text='[{}]The api url.'.format('hipchat'))
    color = models.Field(required=False, display=False,
                         type=click.Choice(['yellow', 'green', 'red', 'purple',
                                            'gray', 'random']),
                         help_text='[{}]The notification color.'.
                         format('hipchat'))
    notify = models.Field(required=False, display=False, default=False,
                          help_text='[{}]The notify channel trigger.'.
                          format('hipchat'))
    url = models.Field(required=False, display=False,
                       help_text='[{}]The target URL.'.format('webhook'))
    headers = models.Field(required=False, display=False,
                           type=models.File('r', lazy=True),
                           help_text='[{}]The http headers.'.format('webhook'))
    server = models.Field(required=False, display=False,
                          help_text='[{}]Server address.'.format('irc'))
    nickname = models.Field(required=False, display=False,
                            help_text='[{}]The irc nick.'.format('irc'))
    target = models.Field(required=False, display=False,
                          help_text='[{}]The distination channels or users.'
                          .format('irc'))

    def _separate(self, kwargs):
        """Remove None-valued and configuration-related keyworded arguments
        """
        self._pop_none(kwargs)
        result = {}
        for field in Resource.config_fields:
            if field in kwargs:
                result[field] = kwargs.pop(field)
                if field in Resource.json_fields:
                    try:
                        data = json.loads(result[field])
                        result[field] = data
                    except ValueError:
                        raise exc.TowerCLIError('Provided json file format '
                                                'invalid. Please recheck.')
        return result

    def _configuration(self, kwargs, config_item):
        """Combine configuration-related keyworded arguments into
        notification_configuration.
        """
        if 'notification_configuration' not in config_item:
            if 'notification_type' not in kwargs:
                return
            nc = kwargs['notification_configuration'] = {}
            for field in Resource.configuration[kwargs['notification_type']]:
                if field not in config_item:
                    raise exc.TowerCLIError('Required config field %s not'
                                            ' provided.' % field)
                else:
                    nc[field] = config_item[field]
        else:
            kwargs['notification_configuration'] = \
                    config_item['notification_configuration']

    @resources.command
    def create(self, **kwargs):
        """Create a notification template.

        All required configuration-related fields (required according to
        notification_type) must be provided.

        Fields in the resource's `identity` tuple are used for a lookup;
        if a match is found, then no-op (unless `force_on_exists` is set) but
        do not fail (unless `fail_on_found` is set).
        """
        config_item = self._separate(kwargs)
        self._configuration(kwargs, config_item)
        return super(Resource, self).create(**kwargs)

    @resources.command
    def modify(self, pk=None, **kwargs):
        """Modify an existing notification template.

        Not all required configuration-related fields (required according to
        notification_type) should be provided.

        Fields in the resource's `identity` tuple can be used in lieu of a
        primary key for a lookup; in such a case, only other fields are
        written.

        To modify unique fields, you must use the primary key for the lookup.
        """
        # Create the resource if needed.
        if pk is None and kwargs.get('create_on_missing', False):
            try:
                self.get(**copy.deepcopy(kwargs))
            except exc.NotFound:
                return self.create(**kwargs)

        # Modify everything except notification type and configuration
        config_item = self._separate(kwargs)
        notification_type = kwargs.pop('notification_type', None)
        debug.log('Modify everything except notification type and'
                  ' configuration', header='details')
        part_result = super(Resource, self).modify(pk=pk, **kwargs)

        # Modify notification type and configuration
        if notification_type is None or \
           notification_type == part_result['notification_type']:
            for item in part_result['notification_configuration']:
                if item not in config_item:
                    config_item[item] = \
                            part_result['notification_configuration'][item]
        if notification_type is None:
            kwargs['notification_type'] = part_result['notification_type']
        else:
            kwargs['notification_type'] = notification_type
        self._configuration(kwargs, config_item)
        debug.log('Modify notification type and configuration',
                  header='details')
        result = super(Resource, self).modify(pk=pk, **kwargs)

        # Update 'changed' field to give general changed info
        if 'changed' in result and 'changed' in part_result:
            result['changed'] = result['changed'] or part_result['changed']
        return result

    @resources.command
    def delete(self, pk=None, **kwargs):
        """Remove the given notification template.

        Note here configuration-related fields like
        'notification_configuration' and 'channels' will not be
        used even provided.

        If `fail_on_missing` is True, then the object's not being found is
        considered a failure; otherwise, a success with no change is reported.
        """
        self._separate(kwargs)
        return super(Resource, self).delete(pk=pk, **kwargs)

    @resources.command
    def list(self, **kwargs):
        """Return a list of notification templates.

        Note here configuration-related fields like
        'notification_configuration' and 'channels' will not be
        used even provided.

        If one or more filters are provided through keyword arguments,
        filter the results accordingly.

        If no filters are provided, return all results.
        """
        self._separate(kwargs)
        return super(Resource, self).list(**kwargs)

    @resources.command
    def get(self, pk=None, **kwargs):
        """Return one and exactly one notification template.

        Note here configuration-related fields like
        'notification_configuration' and 'channels' will not be
        used even provided.

        Lookups may be through a primary key, specified as a positional
        argument, and/or through filters specified through keyword arguments.

        If the number of results does not equal one, raise an exception.
        """
        self._separate(kwargs)
        return super(Resource, self).get(pk=pk, **kwargs)
