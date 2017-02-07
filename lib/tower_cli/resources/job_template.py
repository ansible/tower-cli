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

from __future__ import absolute_import, unicode_literals

import click

from tower_cli import models, resources
from tower_cli.utils import types
from tower_cli.utils import parser


class Resource(models.Resource):
    cli_help = 'Manage job templates.'
    endpoint = '/job_templates/'

    name = models.Field(unique=True)
    description = models.Field(required=False, display=False)
    job_type = models.Field(
        required=False,
        display=False,
        type=click.Choice(['run', 'check', 'scan']),
    )
    inventory = models.Field(type=types.Related('inventory'), required=False)
    project = models.Field(type=types.Related('project'))
    playbook = models.Field()
    machine_credential = models.Field(
        'credential',
        display=False, required=False,
        type=types.Related('credential'),
    )
    cloud_credential = models.Field(type=types.Related('credential'),
                                    required=False, display=False)
    network_credential = models.Field(type=types.Related('credential'),
                                      required=False, display=False)
    forks = models.Field(type=int, required=False, display=False)
    limit = models.Field(required=False, display=False)
    verbosity = models.Field(
        display=False,
        type=types.MappedChoice([
            (0, 'default'),
            (1, 'verbose'),
            (2, 'more_verbose'),
            (3, 'debug'),
            (4, 'connection'),
            (5, 'winrm'),
        ]),
        required=False,
    )
    job_tags = models.Field(required=False, display=False)
    skip_tags = models.Field(required=False, display=False)
    extra_vars = models.Field(required=False, display=False)
    host_config_key = models.Field(
        required=False, display=False,
        help_text='Allow Provisioning Callbacks using this host config key')
    ask_variables_on_launch = models.Field(
        type=bool, required=False, display=False,
        help_text='Prompt user for extra_vars on launch.')
    ask_limit_on_launch = models.Field(
        type=bool, required=False, display=False,
        help_text='Prompt user for host limits on launch.')
    ask_tags_on_launch = models.Field(
        type=bool, required=False, display=False,
        help_text='Prompt user for job tags on launch.')
    ask_skip_tags_on_launch = models.Field(
        type=bool, required=False, display=False,
        help_text='Prompt user for tags to skip on launch.')
    ask_job_type_on_launch = models.Field(
        type=bool, required=False, display=False,
        help_text='Prompt user for job type on launch.')
    ask_inventory_on_launch = models.Field(
        type=bool, required=False, display=False,
        help_text='Prompt user for inventory on launch.')
    ask_credential_on_launch = models.Field(
        type=bool, required=False, display=False,
        help_text='Prompt user for machine credential on launch.')
    become_enabled = models.Field(type=bool, required=False, display=False)

    @resources.command
    @click.option('--extra-vars', required=False, multiple=True,
                  help='Extra variables used by Ansible in YAML or key=value '
                       'format. Use @ to get YAML from a file.')
    def create(self, fail_on_found=False, force_on_exists=False,
               extra_vars=None, **kwargs):
        """Create a job template.
        You may include multiple --extra-vars flags in order to combine
        different sources of extra variables. Start this
        with @ in order to indicate a filename."""
        if extra_vars:
            # combine sources of extra variables, if given
            kwargs['extra_vars'] = parser.process_extra_vars(
                extra_vars, force_json=False
            )
        # Provide a default value for job_type, but only in creation of JT
        if not kwargs.get('job_type', False):
            kwargs['job_type'] = 'run'
        return super(Resource, self).create(
            fail_on_found=fail_on_found, force_on_exists=force_on_exists,
            **kwargs
        )

    @resources.command
    @click.option('--extra-vars', required=False, multiple=True,
                  help='Extra variables used by Ansible in YAML or key=value '
                       'format. Use @ to get YAML from a file.')
    def modify(self, pk=None, create_on_missing=False,
               extra_vars=None, **kwargs):
        """Modify a job template.
        You may include multiple --extra-vars flags in order to combine
        different sources of extra variables. Start this
        with @ in order to indicate a filename."""
        if extra_vars:
            # combine sources of extra variables, if given
            kwargs['extra_vars'] = parser.process_extra_vars(
                extra_vars, force_json=False
            )
        return super(Resource, self).modify(
            pk=pk, create_on_missing=create_on_missing, **kwargs
        )

    @resources.command(use_fields_as_options=False)
    @click.option('--job-template', type=types.Related('job_template'))
    @click.option('--label', type=types.Related('label'))
    def associate_label(self, job_template, label):
        """Associate an label with this job template."""
        return self._assoc('labels', job_template, label)

    @resources.command(use_fields_as_options=False)
    @click.option('--job-template', type=types.Related('job_template'))
    @click.option('--label', type=types.Related('label'))
    def disassociate_label(self, job_template, label):
        """Disassociate an label from this job template."""
        return self._disassoc('labels', job_template, label)

    @resources.command(use_fields_as_options=False)
    @click.option('--job-template', type=types.Related('job_template'))
    @click.option('--notification-template',
                  type=types.Related('notification_template'))
    @click.option('--status', type=click.Choice(['any', 'error', 'success']),
                  required=False, default='any', help='Specify job run status'
                  ' of job template to relate to.')
    def associate_notification_template(self, job_template,
                                        notification_template, status):
        """Associate a notification template from this job template."""
        return self._assoc('notification_templates_%s' % status,
                           job_template, notification_template)

    @resources.command(use_fields_as_options=False)
    @click.option('--job-template', type=types.Related('job_template'))
    @click.option('--notification-template',
                  type=types.Related('notification_template'))
    @click.option('--status', type=click.Choice(['any', 'error', 'success']),
                  required=False, default='any', help='Specify job run status'
                  ' of job template to relate to.')
    def disassociate_notification_template(self, job_template,
                                           notification_template, status):
        """Disassociate a notification template from this job template."""
        return self._disassoc('notification_templates_%s' % status,
                              job_template, notification_template)
