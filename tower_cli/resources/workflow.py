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
from tower_cli.utils.parser import string_to_dict
from tower_cli.utils.exceptions import BadRequest
from tower_cli.conf import settings
from tower_cli.resources.node import NODE_STANDARD_FIELDS, JOB_TYPES

import click


class Resource(models.SurveyResource):
    cli_help = 'Manage workflow job templates.'
    endpoint = '/workflow_job_templates/'
    unified_job_type = '/workflow_jobs/'

    name = models.Field(unique=True)
    description = models.Field(required=False, display=False)
    extra_vars = models.Field(
        type=types.Variables(), required=False, display=False, multiple=True,
        help_text='Extra variables used by Ansible in YAML or key=value '
                  'format. Use @ to get YAML from a file. Use the option '
                  'multiple times to add multiple extra variables')
    organization = models.Field(type=types.Related('organization'),
                                required=False)
    survey_enabled = models.Field(
        type=bool, required=False, display=False,
        help_text='Prompt user for job type on launch.')
    survey_spec = models.Field(
        type=types.Variables(), required=False, display=False,
        help_text='On write commands, perform extra POST to the '
                  'survey_spec endpoint.')

    @staticmethod
    def _workflow_node_structure(node_results):
        '''
        Takes the list results from the API in `node_results` and
        translates this data into a dictionary organized in a
        human-readable heirarchial structure
        '''
        # Build list address translation, and create backlink lists
        node_list_pos = {}
        for i, node_result in enumerate(node_results):
            for rel in ['success', 'failure', 'always']:
                node_result['{0}_backlinks'.format(rel)] = []
            node_list_pos[node_result['id']] = i

        # Populate backlink lists
        for node_result in node_results:
            for rel in ['success', 'failure', 'always']:
                for sub_node_id in node_result['{0}_nodes'.format(rel)]:
                    j = node_list_pos[sub_node_id]
                    node_results[j]['{0}_backlinks'.format(rel)].append(
                        node_result['id'])

        # Find the root nodes
        root_nodes = []
        for node_result in node_results:
            is_root = True
            for rel in ['success', 'failure', 'always']:
                if node_result['{0}_backlinks'.format(rel)] != []:
                    is_root = False
                    break
            if is_root:
                root_nodes.append(node_result['id'])

        # Create network dictionary recursively from root nodes
        def branch_schema(node_id):
            i = node_list_pos[node_id]
            node_dict = node_results[i]
            ret_dict = {}
            for fd in NODE_STANDARD_FIELDS:
                val = node_dict.get(fd, None)
                if val is not None:
                    if fd == 'unified_job_template':
                        job_type = node_dict['summary_fields'][
                            'unified_job_template']['unified_job_type']
                        ujt_key = JOB_TYPES[job_type]
                        ret_dict[ujt_key] = val
                    else:
                        ret_dict[fd] = val
                for rel in ['success', 'failure', 'always']:
                    sub_node_id_list = node_dict['{0}_nodes'.format(rel)]
                    if len(sub_node_id_list) == 0:
                        continue
                    relationship_name = '{0}_nodes'.format(rel)
                    ret_dict[relationship_name] = []
                    for sub_node_id in sub_node_id_list:
                        ret_dict[relationship_name].append(
                            branch_schema(sub_node_id))
            return ret_dict

        schema_dict = []
        for root_node_id in root_nodes:
            schema_dict.append(branch_schema(root_node_id))
        return schema_dict

    def _get_schema(self, wfjt_id):
        """
        Returns a dictionary that represents the node network of the
        workflow job template
        """
        node_res = get_resource('node')
        node_results = node_res.list(workflow_job_template=wfjt_id,
                                     all_pages=True)['results']
        return self._workflow_node_structure(node_results)

    @resources.command(use_fields_as_options=False)
    @click.argument('wfjt', type=types.Related('workflow'))
    @click.argument('node_network', type=types.Variables(), required=False)
    def schema(self, wfjt, node_network=None):
        """
        Convert YAML/JSON content into workflow node objects if
        node_network param is given.
        If not, print a YAML representation of the node network.
        """
        if node_network is None:
            if settings.format == 'human':
                settings.format = 'yaml'
            return self._get_schema(wfjt)

        node_res = get_resource('node')

        def create_node_recursive(node_branch, parent, relationship):
            # Create node with data specified by top-level keys
            create_data = {}
            FK_FIELDS = JOB_TYPES.values() + ['inventory', 'credential']
            for fd in NODE_STANDARD_FIELDS + JOB_TYPES.values():
                if fd in node_branch:
                    if (
                            fd in FK_FIELDS and
                            not isinstance(node_branch[fd], int)):
                        # Node's template was given by name, do lookup
                        ujt_res = get_resource(fd)
                        ujt_data = ujt_res.get(name=node_branch[fd])
                        create_data[fd] = ujt_data['id']
                    else:
                        create_data[fd] = node_branch[fd]
            create_data['workflow_job_template'] = wfjt
            node_data = node_res._get_or_create_child(
                parent, relationship, **create_data)
            # Repeat the process for all sub-branches
            for fd in node_branch:
                for rel in ['success', 'failure', 'always']:
                    if fd.startswith(rel):
                        sub_branch_list = node_branch[fd]
                        if not isinstance(sub_branch_list, list):
                            raise BadRequest(
                                'Sublists in spec must be lists.'
                                'Encountered in {0} at {1}'.format(
                                    fd, sub_branch_list))
                        for sub_branch in sub_branch_list:
                            sub_node_data = create_node_recursive(
                                sub_branch, parent=node_data['id'],
                                relationship=rel)
                            node_res._assoc(
                                node_res._forward_rel_name(rel),
                                node_data['id'], sub_node_data['id'])
                        break
            return node_data

        if hasattr(node_network, 'read'):
            node_network = node_network.read()
        node_network = string_to_dict(
            node_network, allow_kv=False, require_dict=False)

        for base_node in node_network:
            create_node_recursive(base_node, parent=None, relationship=None)

        if settings.format == 'human':
            settings.format = 'yaml'
        return self._get_schema(wfjt)
