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

from tower_cli import models, resources, get_resource
from tower_cli.utils import types
from tower_cli.conf import settings

import click


class Resource(models.Resource):
    cli_help = 'Manage workflow job templates.'
    endpoint = '/workflow_job_templates/'

    name = models.Field(unique=True)
    description = models.Field(required=False, display=False)
    extra_vars = models.Field(
        type=types.Variables(), required=False, display=False,
        help_text='Extra playbook variables to pass to jobs run inside this '
                  'workflow, use "@" to get from file.')
    organization = models.Field(type=types.Related('organization'))

    def _get_schema(self, wfjt_id):
        """
        Returns a dictionary that represents the node network of the
        workflow job template
        """
        node_res = get_resource('node')
        node_results = node_res.list(workflow_job_template=wfjt_id,
                                     all_pages=True)['results']

        # Build list address translation, and create backlink lists 
        node_list_pos = {}
        print 'type ' + str(type(node_results))
        for i, node_result in enumerate(node_results):
            for rel in ['success', 'failure', 'always']:
                node_result['{}_backlinks'.format(rel)] = []
            node_list_pos[node_result['id']] = i

        # Populate backlink lists
        for node_result in node_results:
            for rel in ['success', 'failure', 'always']:
                for sub_node_id in node_result['{}_nodes'.format(rel)]:
                    j = node_list_pos[sub_node_id]
                    node_results[j]['{}_backlinks'.format(rel)].append(
                        node_result['id'])

        # Find the root nodes
        root_nodes = []
        for node_result in node_results:
            is_root = True
            for rel in ['success', 'failure', 'always']:
                if node_result['{}_backlinks'.format(rel)] != []:
                    is_root = False
                    break
            if is_root:
                root_nodes.append(node_result['id'])

        # Create network dictionary recursively from root nodes
        def branch_schema(node_id):
            i = node_list_pos[node_id]
            node_dict = node_results[i]
            ret_dict = {}
            for fd in node_res.STANDARD_FIELDS:
                val = node_dict.get(fd, None)
                if val is not None:
                    if fd == 'unified_job_template':
                        job_type = node_dict['summary_fields'][
                            'unified_job_template']['unified_job_type']
                        ujt_key = node_res.JOB_TYPES[job_type]
                        ret_dict[ujt_key] = val
                    else:
                        ret_dict[fd] = val
                for rel in ['success', 'failure', 'always']:
                    sub_node_id_list = node_dict['{}_nodes'.format(rel)]
                    if len(sub_node_id_list) == 0:
                        continue
                    for sub_node_id in sub_node_id_list:
                        ret_dict['{}_nodes'.format(rel)] = branch_schema(
                            sub_node_id)
            return ret_dict                

        schema_dict = []
        for root_node_id in root_nodes:
            schema_dict.append(branch_schema(root_node_id))
        return schema_dict

    @resources.command(use_fields_as_options=False)
    @click.argument('wfjt', type=types.Related('workflow'))
    @click.argument('node_network', type=types.Variables(), required=False)
    def schema(self, wfjt, node_network=None):
        """
        Convert a YAML/JSON file into workflow node objects if
        `node_network` param is given.
        If not, print a YAML representation of the node network.
        """
        if node_network is None:
            settings.format = 'yaml'
            return self._get_schema(wfjt)

        node_res = get_resource('node')

        def create_node_recursive(node_branch):
            node_data = node_res.create(node_branch)
            for key in node_branch:
                for rel in ['success', 'failure', 'always']:
                    if key.startswith(rel):
                        for sub_branch in node_branch[key]:
                            sub_node_data = create_node_recursive(sub_branch)
                            node_res._assoc(
                                'success_nodes', node_data['id'],
                                sub_node_data['id'])
            return node_data

        for base_node in node_network:
            create_node_recursive(base_node)

        settings.format = 'yaml'
        return self._get_schema(wfjt)

        # return {'changed': True}
