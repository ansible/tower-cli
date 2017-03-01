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


class Resource(models.Resource):
    cli_help = 'Manage users within Ansible Tower.'
    endpoint = '/users/'
    identity = ('username',)

    username = models.Field(unique=True)
    password = models.Field(required=False, display=False)
    email = models.Field(unique=True)
    first_name = models.Field(required=False)
    last_name = models.Field(required=False)
    is_superuser = models.Field(required=False, type=bool)
    is_system_auditor = models.Field(required=False, type=bool)
