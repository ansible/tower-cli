# Copyright 2018, Red Hat, Inc.
# Ryan Petrello <rpetrell@redhat.com>
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


CLIENT_TYPES = [
    'confidential',
    'public'
]

GRANT_TYPES = [
    "authorization-code",
    "implicit",
    "password",
    "client-credentials",
]


class Resource(models.Resource):
    """A resource for OAuth2 applications."""
    cli_help = 'Manage OAuth2 applications.'
    endpoint = '/applications/'
    dependencies = ['organization']

    name = models.Field(unique=True)
    client_type = models.Field(type=click.Choice(CLIENT_TYPES), required=True)
    redirect_uris = models.Field(required=False)
    authorization_grant_type = models.Field(type=click.Choice(GRANT_TYPES), required=True)
    skip_authorization = models.Field(type=click.BOOL, required=False)
    organization = models.Field(type=types.Related('organization'), required=True)
