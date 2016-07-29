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

from tower_cli import get_resource, models, resources
from tower_cli.utils import types, debug, exceptions as exc


class Resource(models.Resource):
    cli_help = 'Manage notification templates within Ansible Tower.'
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
    encrypted_fields = ['password', 'token', 'account_token']

    # notification_configuration-related fields. fields with default values
    # are optional.
    username = models.Field(required=False, display=False,
                            help_text='[{0}]The username.'.format('email'))
    sender = models.Field(required=False, display=False,
                          help_text='[{0}]The sender.'.format('email'))
    recipients = models.Field(required=False, display=False, multiple=True,
                              help_text='[{0}]The recipients.'.format('email'))
    use_tls = models.Field(required=False, display=False, type=click.BOOL,
                           default=False,
                           help_text='[{0}]The tls trigger.'.format('email'))
    host = models.Field(required=False, display=False,
                        help_text='[{0}]The host.'.format('email'))
    use_ssl = models.Field(required=False, display=False, type=click.BOOL,
                           default=False, help_text='[{0}]The ssl trigger.'
                           .format('email/irc'))
    password = models.Field(required=False, display=False, password=True,
                            help_text='[{0}]The password.'.format('email/irc'))
    port = models.Field(required=False, display=False, type=click.INT,
                        help_text='[{0}]The email port.'.format('email/irc'))
    channels = models.Field(required=False, display=False, multiple=True,
                            help_text='[{0}]The channel.'.format('slack'))
    token = models.Field(required=False, display=False, password=True,
                         help_text='[{0}]The token.'.
                         format('slack/pagerduty/hipchat'))
    account_token = models.Field(required=False, display=False, password=True,
                                 help_text='[{0}]The account token.'.
                                 format('twilio'))
    from_number = models.Field(required=False, display=False,
                               help_text='[{0}]The source phone number.'.
                               format('twilio'))
    to_numbers = models.Field(required=False, display=False, multiple=True,
                              help_text='[{0}]The destination SMS numbers.'.
                              format('twilio'))
    account_sid = models.Field(required=False, display=False,
                               help_text='[{0}The account sid.'.
                               format('twilio'))
    subdomain = models.Field(required=False, display=False,
                             help_text='[{0}]The subdomain.'.
                             format('pagerduty'))
    service_key = models.Field(required=False, display=False,
                               help_text='[{0}]The API service/integration'
                               ' key.'.format('pagerduty'))
    client_name = models.Field(required=False, display=False,
                               help_text='[{0}]The client identifier.'.
                               format('pagerduty'))
    message_from = models.Field(required=False, display=False,
                                help_text='[{0}]The label to be shown with '
                                'notification.'.format('hipchat'))
    api_url = models.Field(required=False, display=False,
                           help_text='[{0}]The api url.'.format('hipchat'))
    color = models.Field(required=False, display=False,
                         type=click.Choice(['yellow', 'green', 'red', 'purple',
                                            'gray', 'random']),
                         help_text='[{0}]The notification color.'.
                         format('hipchat'))
    notify = models.Field(required=False, display=False, default=False,
                          help_text='[{0}]The notify channel trigger.'.
                          format('hipchat'))
    url = models.Field(required=False, display=False,
                       help_text='[{0}]The target URL.'.format('webhook'))
    headers = models.Field(required=False, display=False,
                           type=models.File('r', lazy=True),
                           help_text='[{0}]The http headers.'.
                           format('webhook'))
    server = models.Field(required=False, display=False,
                          help_text='[{0}]Server address.'.format('irc'))
    nickname = models.Field(required=False, display=False,
                            help_text='[{0}]The irc nick.'.format('irc'))
    target = models.Field(required=False, display=False,
                          help_text='[{0}]The distination channels or users.'
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
    @click.option('--job-template', type=types.Related('job_template'),
                  required=False, help='The job template to relate to.')
    @click.option('--status', type=click.Choice(['error', 'success']),
                  required=False, help='Specify job run status of job '
                  'template to relate to.')
    def create(self, fail_on_found=False, force_on_exists=False, **kwargs):
        """Create a notification template.

        All required configuration-related fields (required according to
        notification_type) must be provided.

        There are two types of notification template creation: isolatedly
        creating a new notification template and creating a new notification
        template under a job template. Here the two types are discriminated by
        whether to provide --job-template option. --status option controls
        more specific, job-run-status-related association.

        Fields in the resource's `identity` tuple are used for a lookup;
        if a match is found, then no-op (unless `force_on_exists` is set) but
        do not fail (unless `fail_on_found` is set).
        """
        config_item = self._separate(kwargs)
        jt_id = kwargs.pop('job_template', None)
        status = kwargs.pop('status', 'any')
        old_endpoint = self.endpoint
        if jt_id is not None:
            jt = get_resource('job_template')
            jt.get(pk=jt_id)
            try:
                nt_id = self.get(**copy.deepcopy(kwargs))['id']
            except exc.NotFound:
                pass
            else:
                if fail_on_found:
                    raise exc.TowerCLIError('Notification template already '
                                            'exists and fail-on-found is '
                                            'switched on. Please use'
                                            ' "associate_notification" method'
                                            ' of job_template instead.')
                else:
                    debug.log('Notification template already exists, '
                              'associating with job template.',
                              header='details')
                    return jt.associate_notification(jt_id, nt_id,
                                                     status=status)
            self.endpoint = '/job_templates/%d/notification_templates_%s/' %\
                            (jt_id, status)
        self._configuration(kwargs, config_item)
        result = super(Resource, self).create(**kwargs)
        self.endpoint = old_endpoint
        return result

    @resources.command
    def modify(self, pk=None, create_on_missing=False, **kwargs):
        """Modify an existing notification template.

        Not all required configuration-related fields (required according to
        notification_type) should be provided.

        Fields in the resource's `identity` tuple can be used in lieu of a
        primary key for a lookup; in such a case, only other fields are
        written.

        To modify unique fields, you must use the primary key for the lookup.
        """
        # Create the resource if needed.
        if pk is None and create_on_missing:
            try:
                self.get(**copy.deepcopy(kwargs))
            except exc.NotFound:
                return self.create(**kwargs)

        # Modify everything except notification type and configuration
        config_item = self._separate(kwargs)
        notification_type = kwargs.pop('notification_type', None)
        debug.log('Modify everything except notification type and'
                  ' configuration', header='details')
        part_result = super(Resource, self).\
            modify(pk=pk, create_on_missing=create_on_missing, **kwargs)

        # Modify notification type and configuration
        if notification_type is None or \
           notification_type == part_result['notification_type']:
            for item in part_result['notification_configuration']:
                if item not in config_item or not config_item[item]:
                    to_add = part_result['notification_configuration'][item]
                    if not (to_add == '$encrypted$' and
                            item in Resource.encrypted_fields):
                        config_item[item] = to_add
        if notification_type is None:
            kwargs['notification_type'] = part_result['notification_type']
        else:
            kwargs['notification_type'] = notification_type
        self._configuration(kwargs, config_item)
        debug.log('Modify notification type and configuration',
                  header='details')
        result = super(Resource, self).\
            modify(pk=pk, create_on_missing=create_on_missing, **kwargs)

        # Update 'changed' field to give general changed info
        if 'changed' in result and 'changed' in part_result:
            result['changed'] = result['changed'] or part_result['changed']
        return result

    @resources.command
    def delete(self, pk=None, fail_on_missing=False, **kwargs):
        """Remove the given notification template.

        Note here configuration-related fields like
        'notification_configuration' and 'channels' will not be
        used even provided.

        If `fail_on_missing` is True, then the object's not being found is
        considered a failure; otherwise, a success with no change is reported.
        """
        self._separate(kwargs)
        return super(Resource, self).\
            delete(pk=pk, fail_on_missing=fail_on_missing, **kwargs)

    @resources.command
    def list(self, all_pages=False, **kwargs):
        """Return a list of notification templates.

        Note here configuration-related fields like
        'notification_configuration' and 'channels' will not be
        used even provided.

        If one or more filters are provided through keyword arguments,
        filter the results accordingly.

        If no filters are provided, return all results.
        """
        self._separate(kwargs)
        return super(Resource, self).list(all_pages=all_pages, **kwargs)

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
