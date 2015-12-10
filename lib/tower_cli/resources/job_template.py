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

from tower_cli import models
from tower_cli.utils import types
from tower_cli.utils import parser


class Resource(models.Resource):
    cli_help = 'Manage job templates.'
    endpoint = '/job_templates/'

    name = models.Field(unique=True)
    description = models.Field(required=False, display=False)
    job_type = models.Field(
        display=False,
        type=click.Choice(['run', 'check']),
    )
    inventory = models.Field(type=types.Related('inventory'))
    project = models.Field(type=types.Related('project'))
    playbook = models.Field()
    machine_credential = models.Field(
        'credential',
        display=False,
        type=types.Related('credential'),
    )
    cloud_credential = models.Field(type=types.Related('credential'),
                                    required=False, display=False)
    forks = models.Field(type=int, required=False, display=False)
    limit = models.Field(required=False, display=False)
    verbosity = models.Field(
        display=False,
        type=types.MappedChoice([
            (0, 'default'),
            (1, 'verbose'),
            (2, 'debug'),
        ]),
        required=False,
    )
    job_tags = models.Field(required=False, display=False)
    skip_tags = models.Field(required=False, display=False)
    extra_vars = models.Field(required=False, display=False)
    ask_variables_on_launch = models.Field(
        type=bool, required=False, display=False,
        help_text='Prompt user for extra_vars on launch.')
    become_enabled = models.Field(type=bool, required=False, display=False)

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
