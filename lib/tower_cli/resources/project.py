# Copyright 2014, Ansible, Inc.
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

from tower_cli import models
from tower_cli.utils import types


class Resource(models.Resource):
    cli_help = 'Manage projects within Ansible Tower.'
    endpoint = '/projects/'

    name = models.Field(unique=True)
    description = models.Field(required=False, display=False)
    organization = models.Field(type=types.Related('organization'),
                                display=False)
    scm_type = models.Field(
        type=click.Choice(['manual', 'git', 'hg', 'svn']),
    )
    scm_url = models.Field(required=False)
    scm_branch = models.Field(required=False, display=False)
    scm_credential = models.Field('credential',
        display=False,
        required=False,
        type=types.Related('credential'),
    )
    scm_clean = models.Field(type=bool, required=False, display=False)
    scm_delete_on_update = models.Field(type=bool, required=False,
                                        display=False)
    scm_update_on_launch = models.Field(type=bool, required=False,
                                        display=False)

