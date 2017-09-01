# Copyright 2017, Ansible by Red Hat.
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

from tower_cli import models
from tower_cli.cli import types


class Resource(models.Resource):
    """A resource for credential types."""
    cli_help = 'Manage credential types within Ansible Tower.'
    endpoint = '/credential_types/'

    name = models.Field(unique=True)
    description = models.Field(required=False, display=False)
    kind = models.Field(
        help_text='The type of credential type being added. Valid options are: ssh, vault, net, scm, '
                  'cloud and insights. Note only cloud and net can be used for creating credential types.',
        type=click.Choice(['ssh', 'vault', 'net', 'scm', 'cloud', 'insights']),
    )
    managed_by_tower = models.Field(
        type=bool, required=False, read_only=True,
        help_text='Indicating if the credential type is a tower built-in type.')
    inputs = models.Field(
        type=types.StructuredInput(), required=False, display=False,
    )
    injectors = models.Field(
        type=types.StructuredInput(), required=False, display=False,
    )
