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

from tower_cli import models
from tower_cli.cli import types


class Resource(models.Resource):
    """A resource for credentials."""
    cli_help = 'Manage credentials within Ansible Tower.'
    endpoint = '/credentials/'
    identity = ('organization', 'user', 'team', 'name')
    dependencies = ['organization', 'credential_type']

    name = models.Field(unique=True)
    description = models.Field(required=False, display=False)

    # Who owns this credential?
    user = models.Field(display=False, type=types.Related('user'), required=False, no_lookup=True)
    team = models.Field(display=False, type=types.Related('team'), required=False, no_lookup=True)
    organization = models.Field(display=False, type=types.Related('organization'), required=False)

    credential_type = models.Field(type=types.Related('credential_type'))
    inputs = models.Field(type=types.StructuredInput(), required=False, display=False)
