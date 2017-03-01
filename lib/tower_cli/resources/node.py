# Copyright 2016, Ansible by Red Hat
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

from __future__ import absolute_import, unicode_literals

from tower_cli import models, resources
from tower_cli.utils import types
from tower_cli.utils.resource_decorators import unified_job_template_options

import click


class Resource(models.Resource):
    cli_help = 'Manage nodes inside of a workflow job template.'
    endpoint = '/workflow_job_template_nodes/'
    identity = ('id',)

    workflow_job_template = models.Field(
        key='-W', type=types.Related('workflow'))
    inventory = models.Field(
        type=types.Related('inventory'), required=False, display=False)
    credential = models.Field(
        type=types.Related('credential'), required=False, display=False)
    job_type = models.Field(required=False, display=False)
    job_tags = models.Field(required=False, display=False)
    skip_tags = models.Field(required=False, display=False)
    limit = models.Field(required=False, display=False)

    @resources.command(use_fields_as_options=False)
    @unified_job_template_options
    @click.argument('parent', type=types.Related('node'))
    @click.argument('child', type=types.Related('node'))
    def associate_success_node(self, parent, child=None, **kwargs):
        """Add a node to run on success."""
        return self._assoc('success_nodes', parent, child)
