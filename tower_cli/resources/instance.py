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

from tower_cli import models


class Resource(models.Resource):
    """A resource for instances."""
    cli_help = 'Check instances within Ansible Tower.'
    endpoint = '/instances/'

    uuid = models.Field(required=False, display=False, read_only=True)
    hostname = models.Field(required=False, read_only=True)
    version = models.Field(required=False, display=False, read_only=True)
    capacity = models.Field(type=int, required=False, read_only=True)
    consumed_capacity = models.Field(type=int, required=False, read_only=True)

    capacity_adjustment = models.Field(type=float, required=False)
    enabled = models.Field(type=bool, required=False)
    managed_by_policy = models.Field(type=bool, required=False)
