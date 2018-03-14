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

from tower_cli import models
from tower_cli.cli import types


class Resource(models.BaseResource):
    """A resource for OAuth2 tokens."""
    cli_help = 'Manage OAuth2 tokens.'
    endpoint = '/tokens/'
    internal = True

    user = models.Field(type=types.Related('user'), required=True)
    application = models.Field(type=types.Related('application'), required=True)

    created = models.Field(required=False)
    modified = models.Field(required=False)
    token = models.Field(required=False)
    refresh_token = models.Field(required=False)
    expires = models.Field(required=False)
    scope = models.Field(required=False)
