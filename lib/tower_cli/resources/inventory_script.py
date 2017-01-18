# Copyright 2016, Ansible by Red Hat.
# Aaron Tan <sitan@redhat.com>
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

from tower_cli import models
from tower_cli.utils import types


class Resource(models.Resource):
    cli_help = 'Manage inventory scripts within Ansible Tower.'
    endpoint = '/inventory_scripts/'

    name = models.Field(unique=True)
    description = models.Field(required=False, display=False)
    script = models.Field(
        type=types.Variables(), display=False,
        help_text='Script code to fetch inventory, prefix with "@" to '
                  'use contents of file for this field.')
    organization = models.Field(type=types.Related('organization'),
                                display=False)
