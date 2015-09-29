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
        default='run',
        display=False,
        show_default=True,
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
    become_enabled = models.Field(type=bool, required=False, display=False)

    @resources.command
    @click.option('--extra-vars', required=False, multiple=True,
                  help='yaml format text that contains extra variables '
                       'to pass on. Use @ to get these from a file.')
    def create(self, extra_vars=None, *args, **kwargs):
        """Create a job template.
        You may include multiple --extra-vars flags in order to combine
        different sources of extra variables. Start this
        with @ in order to indicate a filename."""
        if extra_vars:
            # combine sources of extra variables, if given
            kwargs['extra_vars'] = parser.extra_vars_loader_wrapper(extra_vars)
        return super(Resource, self).create(*args, **kwargs)

    @resources.command
    def modify(self, pk=None, *args, **kwargs):
        """Modify a job template.
        You may only include one --extra-vars flag with this command, and
        whatever you provde will overwrite the existing field. Start this
        with @ in order to indicate a filename."""
        if 'extra_vars' in kwargs:
            # read from file, if given
            kwargs['extra_vars'] = \
                parser.file_or_yaml_split(kwargs['extra_vars'])
        return super(Resource, self).modify(pk=pk, *args, **kwargs)
